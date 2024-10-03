#!/usr/bin/env python3
"""For reviewing pull requests, run `spack install` on recipes changed current PR"""
# Copyright 2024, Bernhard Kaindl
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import argparse
import re
import subprocess
import sys
from logging import INFO, basicConfig, info
from time import sleep
from typing import List, Tuple

import pexpect


def get_os_info() -> Tuple[str, str, str]:
    """Get the OS information."""
    about_build_host = ""
    os_name = ""
    os_version_id = ""
    with open("/etc/os-release", encoding="utf-8") as f:
        os_release = f.read()
        for line in os_release.split("\n"):
            if line.startswith("PRETTY_NAME="):
                about_build_host += " on " + line.split("=")[1].strip().strip('"')
            if line.startswith("VERSION_ID="):
                os_version_id = line.split("=")[1].strip().strip('"')
            if line.startswith("NAME="):
                os_name = line.split("=")[1].strip().strip('"')
    return about_build_host, os_name, os_version_id


def get_safe_versions(spec):
    """Find the safe versions of the specs. Parse the output of `bin/spack versions --safe`:
    bin/spack versions --safe wget
    ==> Safe versions (already checksummed):
    master  2.4.1  2.3  2.2  2.1  2.0  1.3
    """
    safe_versions = []
    # FIXME: The spec may contain variants, etc, use a regex to remove them.
    recipe = spec.split("+")[0]  # Remove variants, and more as they are added to the spec.
    err, stdout, _ = run(["bin/spack", "versions", "--safe", recipe])
    if err == 0:
        for line in stdout.split("\n"):
            if line.startswith("==> Safe versions"):
                continue
            safe_versions.extend(line.split())

    # Remove the versions that should be skipped (development branches often fail to build):
    for skip_version in ["master", "develop", "main"]:
        if skip_version in safe_versions:
            safe_versions.remove(skip_version)

    return safe_versions


def find_already_installed(recipes):
    """List the installed packages."""
    installed = []
    findings = []
    for recipe in recipes:
        err, stdout, _ = run(["bin/spack", "find", "--no-groups", "-v", "-I", recipe])
        if err == 0:
            print(stdout)
            installed.append(recipe)
            findings.append(stdout.replace(" build_system=python_pip", ""))
    return installed, findings


def spack_uninstall_packages(installed):
    """Uninstall the installed packages."""
    for recipe in installed:
        ret, out, err = run(["bin/spack", "uninstall", "-ya", "--dependents", recipe])
        print(out)
        if ret != 0:
            print(err or out)
            sys.exit(ret)


def spawn(command, args):
    """Spawn a command."""
    print(" ".join([command, *args]))
    child = pexpect.spawnu(command, args)
    child.interact()
    child.expect(pexpect.EOF)
    child.close()
    return child.exitstatus


def run(command: List[str], check=False) -> Tuple[int, str, str]:
    """Run a command and return the output."""
    info(" ".join(command))
    cmd: subprocess.CompletedProcess[str] = subprocess.run(
        command, check=check, text=True, capture_output=True
    )
    return cmd.returncode, cmd.stdout.strip(), cmd.stderr.strip()


def get_specs_to_check():
    """Check if the current branch is up-to-date with the remote branch.

    Check if the current branch is up-to-date with the remote branch.
    On errors and if not up-to-date, return an error exit code.
    """
    changed_files = []
    changed_recipe = ""
    recipe_paths = []
    recipes = []
    specs = []
    variants = []
    versions = []
    next_line_is_version = False

    # The most reliable way to get the PR diff is to use the GitHub CLI:
    err, stdout, stderr = run(["gh", "pr", "diff"])
    if err or stderr:
        print(stderr or stdout)
        sys.exit(err)

    for line in stdout.split("\n"):
        if line.startswith("diff --git"):
            changed_recipe = ""
            versions = []
            variants = []
            next_line_is_version = False
            continue
        if line[0] != "+":
            continue
        # Check if the line is a path to a changed file:
        changed_path = re.search(r"\+\+\+ b/(.*)", line)
        if changed_path:
            changed_file = changed_path.group(1)
            changed_files.append(changed_file)
            recipe = re.search(r"var/spack/repos/builtin/packages/(.*)/package.py", changed_file)
            if recipe:
                recipe_paths.append(changed_file)
                changed_recipe = recipe.group(1)
                recipes.append(changed_recipe)
                specs.append(changed_recipe)
            continue
        if not changed_recipe:
            continue

        # Get the list of new and changed versions from the PR diff:
        version_start = re.search(r"version\($", line)
        if version_start:
            next_line_is_version = True
            continue
        version = re.search(r'version\("(.+)", ', line)
        if next_line_is_version or version:
            next_line_is_version = False
            version = version or re.search(r'"(.+)"', line)
            if version:
                spec = changed_recipe + "@" + version.group(1)
                # Add the version to the specs to build:
                if changed_recipe in specs:
                    specs.remove(changed_recipe)
                specs.append(spec)
            continue

        # TODO: Add support for wrapping the variant in single quotes and on the next line.
        # TODO: Add support for multi variants.
        # or, better:
        # TODO: Add support for getting the list of new and changed variants from spack:
        variant = re.search(r'variant\("(.+)", ', line)
        if variant:
            variant_str = "+" + variant.group(1)
            variants.append(variant_str)
            # Add the version to the specs to build:
            if changed_recipe in specs:
                specs.remove(changed_recipe)
            specs.append(changed_recipe + variant_str)

            for version in versions:
                spec = changed_recipe + variant_str + "@" + version
                specs.append(spec)

    return specs


def expand_specs_to_check_package_versions(specs_to_check, max_versions) -> List[str]:
    """Expand the specs to check by adding the safe versions of the packages."""
    for spec in specs_to_check.copy():
        recipe = spec.split("@")[0]
        versions = get_safe_versions(recipe)
        if versions:
            specs_to_check.remove(spec)
            specs_to_check.extend([recipe + "@" + version for version in versions[:max_versions]])
    return specs_to_check


def check_all_downloads(specs):
    """Check if the sources for installing those specs can be downloaded."""
    fetch_flags = ["--fresh", "--fresh-roots", "--deprecated"]
    for spec in specs:
        info(f"download+sha256 check {specs.index(spec) + 1} of {len(specs)}: {spec}")
        ret = spawn("bin/spack", ["fetch", *fetch_flags, spec])
        if ret:
            return ret
    return 0


def spack_install(specs):
    """Install the packages."""
    passed = []
    failed = []
    for spec in specs:
        if spec.startswith("composable-kernel"):
            print("Skipping composable-kernel: Without a fast GPU, it takes too long.")
            continue

        print(f"\nspack install -v {spec} # {specs.index(spec) + 1} of {len(specs)}\n")
        # TODO: Add support for installing the packages in a container, sandbox, or remote host.

        # TODO: Concertize the the spec before installing to record the exact dependencies.

        cmd = ["install", "-v", "--fail-fast", "--deprecated", spec]
        ret = spawn("bin/spack", cmd)
        if ret == 0:
            print(f"\n------------------------- Passed {spec} -------------------------")
            passed.append(spec)
        else:
            print(f"\n------------------------- FAILED {spec} -------------------------")
            print("\nFailed command:", " ".join(["bin/spack", *cmd]) + "\n")
            sleep(5)
            failed.append(spec)

    return passed, failed


def parse_args() -> argparse.Namespace:
    """Run spack install on recipes changed in the current branch from develop."""
    basicConfig(format="%(message)s", level=INFO)

    # Parse the command line arguments using argparse.
    # The arguments are:
    # -l, --label: Label the PR with the results if successful.
    # -d, --download: Download and checksum check only.
    # -s=<versions>, --safe-versions=<versions>: Install <versions> safe versions of the packages.
    # -u, --uninstall: Uninstall the installed packages.
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        "-l", "--label-success", action="store_true", help="Label the PR on success."
    )
    argparser.add_argument(
        "-s",
        "--safe-versions",
        type=int,
        help="Install <versions> safe versions of the packages.",
    )
    argparser.add_argument(
        "-d", "--download", action="store_true", help="Download and checksum check only"
    )
    argparser.add_argument(
        "-u", "--uninstall", action="store_true", help="Uninstall the installed packages."
    )
    return argparser.parse_args()


def main(args) -> int:
    """Run the main code for the script using the parsed command line flags"""
    # TODO:
    # - Add support for installing the packages in a container, sandbox, or remote host.
    #   Use pxssh module of pexpect: https://pexpect.readthedocs.io/en/stable/api/pxssh.html

    # Get the specs to check.
    specs_to_check = get_specs_to_check()
    info("specs to check: %s", " ".join(specs_to_check))

    # Check if the specs have versions and add the versions to the specs to check.

    if args.safe_versions:
        print("Checking for existing safe versions of the packages to build or download")
        # Limit the number of versions to check to 6.
        specs_to_check = expand_specs_to_check_package_versions(specs_to_check, args.safe_versions)

    # Check if the sources for installing those specs can be downloaded.
    # This can be skipped as some packages like rust don't have a checksum,
    # and the download is done by the install command anyway.
    if args.download:
        return check_all_downloads(specs_to_check)

    # Check if specs are already installed and ask if they should be uninstalled.
    installed, findings = find_already_installed(specs_to_check)
    if installed:
        print("These specs are already installed:")
        print("\n".join(findings))
        if args.uninstall:
            if input("Uninstall them? [y/n]: ").lower() == "y":
                spack_uninstall_packages(installed)
                installed = []

    for already_installed_pkg in installed:
        specs_to_check.remove(already_installed_pkg)

    passed, failed = spack_install(specs_to_check)

    # Generate a report in markdown format for cut-and-paste into the PR comment:
    about_build_host, os_name, os_version_id = get_os_info()

    print(f"Build results{about_build_host}:")
    print("```py")
    if passed + installed:
        done = " ".join(installed + passed)
        if len(done) < 80:
            print("Passed:", done)
        else:
            print("Passed:\n" + "\n".join(installed + passed))
    if failed:
        print("\nFailed:", " ".join(failed))
        # TODO: Add support for showing details about the failed specs.

    # TODO: Add showing "group" infos like compiler version, cmake version, etc.:
    print("spack find -v:")
    err, stdout, stderr = run(["bin/spack", "find", "-v", *(installed + passed)])
    if not err:
        print(stdout)
    else:
        print(stderr or stdout)
    print("```")
    print("Generated by:")
    print("https://github.com/spack/build-quality-tools/blob/main/build_pr_changes.py")
    if failed or not passed + installed:
        return 1
    if args.label_success:
        print("All specs passed, labeling the PR.")
        run(["gh", "pr", "edit", "--add-label", f"Built on {os_name} {os_version_id}"])
    return 0


def parse_args_and_run():
    """Parse the command line arguments and run the main function."""
    ret = main(parse_args())
    if ret:
        sys.exit(ret)


if __name__ == "__main__":
    parse_args_and_run()
