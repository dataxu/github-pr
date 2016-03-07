#!/usr/bin/env python
import github_pr
import os
import argparse
from github import Github


def main():
    """ For executing as a script. """

    default_token = os.getenv('GITHUB_API_TOKEN')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Show PRs or a specific PR

    github-pr list -r dataxu/test_repo
    github-pr list -r dataxu/test_repo -n 17

    - Filters - can be used alone or together
        --filters
            * owner - This will return a list of PRs from the repo that are owned by the github-user
            * status - returns PRs with a specifc status, one of (success, failure, error, pending)
            * label - returns PRs with a specifc label
            * comment - returns PRs that have at least one comment matching a given string
      github-pr list -r dataxu/test_repo --filters 'filter1_name=filter1_value,filter2_name=filter2_value'

      github-pr list -r dataxu/test_repo --filters 'owner=frankenstein,status=success,comment=:pitchfork:'
            This returns the number of all PRs in the given repo owned by frankenstein with the status success and containing any comments that have ":pitchfork:"

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
        """)
    parser.add_argument('action', choices=['create', 'list', 'merge', 'comment', 'delete', 'update'], help='action to take')
    parser.add_argument('-r', '--repo', required=True, help='the owner/name of the repository')
    parser.add_argument('-t', '--title', help='the title of the pr')
    parser.add_argument('-f', '--files', action='store_true', default=False, help='list files in the PR')
    parser.add_argument('-n', '--number', type=int, help='pr number')
    parser.add_argument('-l', '--label', nargs='+', help='label(s) to add/apply to the pr (one or more, space separated), or find a list of prs with matching labels (with list action)')
    parser.add_argument('-c', '--comments', action='store_true', help='added to list, to return list of comments')
    parser.add_argument('--filters', help='add this to the list function with collection of options you want to filter your results for', type=str)
    parser.add_argument('--base', default='master', help='branch the pr is against')
    parser.add_argument('--head', help='branch the pr is of')
    parser.add_argument('--body', default='', help='the description of the pr')
    parser.add_argument('--replacelabels', action='store_true', help='replace ALL labels during an update')
    parser.add_argument('--token', default=default_token, help='api token to use')
    parser.add_argument('--numberonly', action='store_true', help='only return the numbers of the PRs during the list action')
    parser.add_argument('--table', action='store_true', help='show a table of output instead of pretty. not compatible with numberonly')
    parser.add_argument('--tableformat', default='simple', help='format of table to use')
    parser.add_argument('--noheaders', action='store_true', help='remove headers from table view. best for programmatic use of this script')
    parser.add_argument('--noratelimit', action='store_true', help="don't show the rate limit")

    args = vars(parser.parse_args())

    if 'action' in args and args['action'] == 'create':
        github_pr.github_create_pr(**args)

    elif 'action' in args and args['action'] == 'list':
        github_pr.github_list_prs(**args)

    elif 'action' in args and args['action'] == 'merge':
        if 'number' in args and args['number']:
            github_pr.github_merge_pr_by_number(**args)
        else:
            github_pr.github_merge_pr_by_branch(**args)

    elif 'action' in args and args['action'] == 'comment':
        github_pr.github_comment_pr(**args)

    elif 'action' in args and args['action'] == 'delete':
        github_pr.github_delete_pr(**args)

    elif 'action' in args and args['action'] == 'update':
        github_pr.github_update_pr(**args)

    gh = Github(args['token'])

    if (('numberonly' in args) and not args['numberonly']):
        if (('noratelimit' in args) and not args['noratelimit']):
            print "Github Rate Limiting: %d remaining of max %d" % (gh.rate_limiting[0], gh.rate_limiting[1])

if __name__ == '__main__':
    main()
