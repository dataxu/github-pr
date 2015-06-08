# github-pr

github-pr is a CLI utility script for working with GitHub pull
requests. It's built on top of the most excellent
[PyGithub](https://github.com/PyGithub/PyGithub).

## Installation:

    pip install git+ssh://git@github.com/dataxu/github-pr.git

## Prerequisites:

    export GITHUB_API_TOKEN=<your GitHub API token value>

## Examples:

Show PRs or a specific PR

    github-pr list -r dataxu/test_repo
    github-pr list -r dataxu/test_repo -n 17

Create a PR

    github-pr create -r dataxu/test_repo -t "PR Title" --head "my-test-branch" --body 'Description Line 1<br/>Line2'

Create a PR from a fork

    github-pr create -r dataxu/test_repo -t "PR Title" --head "my-fork:my-test-branch"

Comment on a PR

    github-pr comment -r dataxu/test_repo -n 17 --body ":shipit:"

Merge a PR by PR number

    github-pr merge -r dataxu/test_repo -n 17

Merge a PR by branch

    github-pr merge -r dataxu/test_repo --head dev-my-branch-name
    github-pr merge -r dataxu/test_repo --head dev-another-branch --base branch-that-is-not-master

Delete a PR

    github-pr delete -r dataxu/test_repo -n 17
