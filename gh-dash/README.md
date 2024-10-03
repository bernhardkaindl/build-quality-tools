# gh-dash

✨ A GitHub (`gh`) CLI extension to display a dashboard
with **pull requests** and **issues** by
[GitHub filters](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
you care about.

It can be configured for the needs of spack
[spack pull requests](https://github.com/spack/spack/pulls) as well.

See [config.yml](config.yml) for an example config that sets the
spack repository path to `~/spack` and gives you a selection of
filters for PRs to use when reviewing PRs.

The default configuration has some useful key bindings:

- `d` displays the diff of the PR like `gh pr diff` would do for the selected PR.
- `v` opens an editor in the right lower corrner for approving the PR.
- `m` opens a confirmation message (Y/n) for merging the PR.
- `q` and `ESC` cancel or quit the current action.

Using the example configuration, I added one useful feature:

- `b` checks out the selected PR, and starts a Bash sub-shell.
  - TODO: When doing so, save any uncommitted changes to a sub-branch and restore it afterwards

This all feels very `vi`-like, and `git diff` can be spiced up by configuring
it to use [delta](https://dandavison.github.io/delta/introduction.html):
<img src="https://user-images.githubusercontent.com/52205/86275526-76792100-bba1-11ea-9e78-6be9baa80b29.png">

For proper glyphs for the pull request status in `gh dash`,
install a [Nerdfont](https://www.nerdfonts.com)!

Here is a demo of how `gh dash` should look with one with a [Nerdfont](https://www.nerdfonts.com):
<img src="https://user-images.githubusercontent.com/6196971/198704107-6775a0ba-669d-418b-9ae9-59228aaa84d1.gif">

## ✨ Feature summary

- 🌅 fully configurable - define sections using
[GitHub filters](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
- ⚡️ act on prs and issues with checkout, comment, open, merge, diff, etc...
- ⌨️ set custom actions with new keybindings
- 🔭 view details about a pr/issue with a detailed sidebar
- 🪟 multiple configuration files to switch between different dashboards

## 📦 Installation

1. Install the `gh` CLI - see the [installation](https://github.com/cli/cli#installation)
2. Install this extension:

   ```sh
   gh extension install dlvhdr/gh-dash
   ```

3. To get the icons to render properly you should download and install
   a Nerd font from <https://www.nerdfonts.com/>.
   Then, select that font as your font for the terminal.

4. Optionally install the sample config file provided in this repo:

   ```sh
   install -D gh-dash/config.yml ~/.config/gh-dash/config.yml
   ```

## ⚡️ Usage

Run

```sh
gh dash
```

Then press <kbd>?</kbd> for help. Run `gh dash --help` for more info:

## ⚙️ Configuring

See the [config section](https://github.com/dlvhdr/gh-dash/?tab=readme-ov-file#%EF%B8%8F-configuring) in the
[project](https://github.com/dlvhdr/gh-dash)'s
[README.md](https://github.com/dlvhdr/gh-dash/blob/main/README.md)
for configuring gh-dash.
