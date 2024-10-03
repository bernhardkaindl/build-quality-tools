#!/usr/bin/env bash
set -ux
PR=$1
CURRENT_BRANCH=$(git branch --show-current)
TTY=$(tty|tr / -)

git checkout -b "$CURRENT_BRANCH-gh-dash-$TTY-$$" &&
    git commit -n --allow-empty -m "gh-dash stash index-save for review of $PR" &&
    git commit -n --allow-empty -am "gh-dash stash all-save for review of $PR" &&
    gh pr checkout "$PR" || {
        echo "gh pr checkout {{.PrNumber}} failed"
        git checkout "$CURRENT_BRANCH"
        git branch -D "$CURRENT_BRANCH-gh-dash-$TTY-$$"
        sleep 5
        exit 1
    } &&
    git log --oneline --graph --decorate --all -n 10

export PR=$PR
export debian_chroot=$PR
bash -i
# shellcheck disable=SC2015
git checkout "$CURRENT_BRANCH-gh-dash-$TTY-$$" &&
    git reset --mixed HEAD~1 &&
    git reset --soft HEAD~1 &&
    git checkout "$CURRENT_BRANCH" &&
    git branch -D "$CURRENT_BRANCH-gh-dash-$TTY-$$" || {
        echo "restoring previous branch state failed"
        sleep 5
        exit 1
    }
