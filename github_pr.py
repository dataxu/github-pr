#!/usr/bin/env python
import argparse
import sys
import os
from tabulate import tabulate
from github import Github


def _check_required_fields(required, **args):
    for i in required:
        if args[i] is None:
            print 'Error: %s parameter not set' % i
            sys.exit(1)


def _print_prs(prs, **args):
    if 'table' in args and args['table']:
        _print_prs_table(prs, **args)
    else:
        for pr in prs:
            _print_pr(pr, **args)

def _print_prs_table(prs, **args):
    prs_data = []
    table_headers = ["#", "State", "Status", "Merge", "Base", "Head", "Title"]
    for pr in prs:
        status = "none"
        try:
            status_obj = pr.get_commits().reversed[0].get_statuses()[0]
            status = status_obj.state
        except Exception as e:
            pass
        prs_data.append([pr.number, pr.state, status, pr.mergeable_state, pr.base.ref, pr.head.ref, pr.title.encode('ascii', errors='ignore')])
    if 'noheaders' in args and args['noheaders']:
        print tabulate(prs_data, tablefmt=args['tableformat'])
    else:
        print tabulate(prs_data, headers=table_headers, tablefmt=args['tableformat'])

def _print_pr(pr, **args):
    if 'numberonly' in args and args['numberonly']:
        print "%d" % pr.number
    else:
        print "#%d [%s] %10s <- %-30s    %s" % (pr.number, pr.state, pr.base.ref, pr.head.ref, pr.title.encode('ascii', errors='ignore'))
        if 'matching_files' in args:
            for f in args['matching_files']:
                print f


def _load_pr(**args):
    _check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_pull(args['number'])


def _load_prs_by_branch(**args):
    _check_required_fields(['token', 'repo', 'head'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    prs = [pr for pr in repo.get_pulls() if pr.head.ref == args['head'] and pr.base.ref == args['base']]
    if len(prs) is not 1:
        print "Probable error, found {0} pull(s) from {1} -> {2} (expected 1)".format(len(prs), args['head'], args['base'])
        _print_prs(prs, **args)
    return prs


def _load_issue(**args):
    """Load the PR as an issue to enable actions like set_labels"""
    _check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_issue(args['number'])


def github_create_pr(**args):
    _check_required_fields(['token', 'repo', 'title', 'body', 'base', 'head'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    pr = repo.create_pull(title=args['title'], body=args['body'], base=args['base'], head=args['head'])
    if 'lable' in args and args['label']:
        args['number'] = pr.number
        github_add_labels(**args)
    _print_pr(pr, **args)


def github_list_prs(**args):
    _check_required_fields(['token', 'repo'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])

    if 'number' in args and args['number']:
        pr = repo.get_pull(args['number'])
        if 'files' in args and args['files']:
            pr_files = pr.get_files()
            args['matching_files'] = [f.filename for f in pr_files]
        _print_prs([pr], **args)
    elif 'label' in args and args['label']:
        label_list = [repo.get_label(label) for label in args['label']]
        prs = [repo.get_pull(i.number) for i in repo.get_issues(labels=label_list) if i.pull_request]
        _print_prs(prs, **args)
    elif 'head' in args and args['head']:
        prs = _load_prs_by_branch(**args)
        _print_prs(prs, **args)
    else:
        prs = repo.get_pulls()
        _print_prs(prs, **args)


def github_merge_pr_by_number(**args):
    _check_required_fields(['token', 'repo', 'number'], **args)
    pr = _load_pr(**args)
    pr.merge()


def github_merge_pr_by_branch(**args):
    _check_required_fields(['token', 'repo', 'head'], **args)
    pr = _load_prs_by_branch(**args)[0]
    pr.merge()


def github_comment_pr(**args):
    _check_required_fields(['body'], **args)
    pr = _load_pr(**args)
    pr.create_issue_comment(args['body'])


def github_delete_pr(**args):
    pr = _load_pr(**args)
    pr.edit(state='closed')


def github_add_labels(**args):
    issue = _load_issue(**args)
    if (('replacelabels' in args) and not args['replacelabels']):
        for label in issue.labels:
            args['label'].append(label.name)
    issue.set_labels(*args['label'])


def github_update_pr(**args):
    was_not_updated = True
    pr = _load_pr(**args)

    edit_params = {}
    if 'title' in args and args['title']:
        edit_params['title'] = args['title']
    if 'body' in args and args['body']:
        edit_params['body'] = args['body']

    if len(edit_params.keys()):
        pr.edit(**edit_params)
        was_not_updated = False

    if 'label' in args and args['label']:
        github_add_labels(**args)
        was_not_updated = False

    if was_not_updated:
        print "Warning: PR %d was NOT updated, no title or body to edit provided" % args['number']

def main():
    """ For executing as a script. """

    default_token = os.getenv('GITHUB_API_TOKEN')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
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
        """)
    parser.add_argument('action', choices=['create', 'list', 'merge', 'comment', 'delete', 'update'], help='action to take')
    parser.add_argument('-r', '--repo', required=True, help='the owner/name of the repository')
    parser.add_argument('-t', '--title', help='the title of the pr')
    parser.add_argument('-f', '--files', action='store_true', default=False, help='list files in the PR')
    parser.add_argument('-n', '--number', type=int, help='pr number')
    parser.add_argument('-l', '--label', nargs='+', help='label(s) to add/apply to the pr (one or more, space separated), or find a list of prs with matching labels (with list action)')
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
        github_create_pr(**args)

    elif 'action' in args and args['action'] == 'list':
        github_list_prs(**args)

    elif 'action' in args and args['action'] == 'merge':
        if 'number' in args and args['number']:
            github_merge_pr_by_number(**args)
        else:
            github_merge_pr_by_branch(**args)

    elif 'action' in args and args['action'] == 'comment':
        github_comment_pr(**args)

    elif 'action' in args and args['action'] == 'delete':
        github_delete_pr(**args)

    elif 'action' in args and args['action'] == 'update':
        github_update_pr(**args)

    gh = Github(args['token'])
    if not args['numberonly'] and not args['noratelimit']:
        print "Github Rate Limiting: %d remaining of max %d" % (gh.rate_limiting[0], gh.rate_limiting[1])

if __name__ == '__main__':
    main()
