# github-pr

github-pr is a CLI utility script for working with pull requests built on top of PyGithub

## Examples:

Show PRs or a specific PR

    ./scripts/github-pr list -r dataxu/dcommand
    ./scripts/github-pr list -r dataxu/dcommand -n 17

Create a PR

    ./scripts/github-pr create -r dataxu/dcommand -t "PR Title" --head "my-test-branch" --body 'Description Line 1<br/>Line2'

Create a PR from a fork

    ./scripts/github-pr create -r dataxu/dcommand -t "PR Title" --head "my-fork:my-test-branch"

Comment on a PR

    ./scripts/github-pr comment -r dataxu/dcommand -n 17 --body ":shipit:"

Merge a PR by PR number

    ./scripts/github-pr merge -r dataxu/dcommand -n 17

Merge a PR by branch

    ./scripts/github-pr merge -r dataxu/dcommand --head dev-my-branch-name
    ./scripts/github-pr merge -r dataxu/dcommand --head dev-another-branch --base branch-that-is-not-master

Delete a PR

    ./scripts/github-pr delete -r dataxu/dcommand -n 17
