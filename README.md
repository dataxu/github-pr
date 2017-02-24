# github-pr

github-pr is a CLI utility script for working with GitHub pull
requests. It's built on top of the most excellent
[PyGithub](https://github.com/PyGithub/PyGithub).

## Installation:

    # from pypi
    pip install github-pr

    # from github
    pip install git+ssh://git@github.com/dataxu/github-pr.git

    # from source
    python setup.py install

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
    
Check conditional status checks 

_This check only looks at comments AFTER the latest commit, to validate that the most recent code (most recent git sha pushed to the PR) has been peer reviewed!!!_
    
This will check to make sure that the owner can not apply a shipable comment on their own code   

    github-pr check-condition -r dataxu/dcommand -n 84 --condition-non-owner-merger
    
This takes the local path to a file containing github usernames, one per line, and checks to make sure the shipit comment came from one of these usernames who is an approved merger   
        
    github-pr check-condition -r dataxu/dcommand -n84 --condition-approved-mergers-file=<MAINTAINERS FILE>
    
The following takes a SPACE-separated list, without quotes or braces. This will check that a comment containing a :shipit: (the default, or other defined comment if merge_comment is set) comes from a user in the provided list passed on the commandline.
    
    github-pr check-condition -r dataxu/dcommand -n 84 --condition-approved-mergers ned_flanders marge_simpson
    


This code was originally developed at [DataXu](https://www.dataxu.com/) and released as open source under the New BSD License.
