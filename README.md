# ✨ Spack build quality review tools

## 🌅 Introduction on using the GitHub CLI (`gh`)

Quick start:

- Install `gh` using `spack install gh` or any other means: <http://cli.github.com>
- Run `gh auth login`: The URL it tries to open into your browser and login
- In your `spack` checkout directory:
- Run `gh pr checkout <PR number>` for checking out a PR to review.
- Run `gh pr review --approve -b "Tested in my environment"` to approve a PR
- Run `gh pr merge --auto --squash` to merge it (enables auto-merge if not ready yet)

## 📝 Tools for checking pull request quality

### ⚡️ [`build_pr_changes.py`](build_pr_changes.py)

Run the script
[build_pr_changes.py](build_pr_changes.py)
found in this repository to install the changes of the PR checked out.

It depends on `gh` to be set up and the PR checked out with `gh pr checkout <PR number>`.
With it, it:

- Gets the PR diff using `gh pr diff`
- Looks for changed and new versions in the PR diff to install
- Looks for changed and new variants in the PR diff to install
- Checks the checksums of all changed and new versions before the build.
- Can also build all versions of recipes if indicated.
- Build each version and variant found from the diff and report the result.
- The result is ready to be pasted into a Pull request review.
- In the future, it could even submit the review directly using the `gh` CLI.

## 🪟 `gh dash`

✨ A GitHub (`gh`) CLI extension to display a dashboard with
**pull requests** and **issues** by
[GitHub filters](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
you care about.

It can be configured for the needs of spack
[spack pull requests](https://github.com/spack/spack/pulls) as well.

Using the example configuration, the key binding `b` checks out the
selected PR, and starts a sub-shell.

In the shell with the PR checked out, you can run
[build_pr_changes.py](build_pr_changes.py) to build the PR and submit the results.

See [gh-dash/README.md](gh-dash/README.md) for an introduction.

<img src="https://user-images.githubusercontent.com/6196971/198704107-6775a0ba-669d-418b-9ae9-59228aaa84d1.gif">
