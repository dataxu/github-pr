#!/usr/bin/env python
import argparse
from datetime import datetime
import pytz
from tzlocal import get_localzone
import sys
import os
import re
from tabulate import tabulate
from github import Github


class NoApproversError(Exception):
    pass


class OwnerCannotShipError(Exception):
    pass


class NoMergeCommentError(Exception):
    pass


def check_required_fields(required, **args):
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
    table_headers = ["#", "State", "Status", "Merge", "BaseFork", "Base", "HeadFork", "Head", "Title"]
    for pr in prs:
        status = "none"
        try:
            status_obj = pr.get_commits().reversed[0].get_statuses()[0]
            status = status_obj.state
        except Exception as e:
            pass
        prs_data.append([pr.number, pr.state, status, pr.mergeable_state, pr.base.repo.owner.login, pr.base.ref, pr.head.repo.owner.login, pr.head.ref, pr.title.encode('ascii', errors='ignore')])
    if 'noheaders' in args and args['noheaders']:
        print tabulate(prs_data, tablefmt=args['tableformat'])
    else:
        print tabulate(prs_data, headers=table_headers, tablefmt=args['tableformat'])


def _print_pr(pr, **args):
    if 'numberonly' in args and args['numberonly']:
        print "%d" % pr.number
    elif 'comments' in args and args['comments']:
        for comment in pr.get_comments():
            print "#%d : Comment - %s" % (pr.number, comment.body)
    else:
        print "#%d [%s] %10s:%s <- %s:%-30s    %s" % (pr.number, pr.state, pr.base.repo.owner.login, pr.base.ref, pr.head.repo.owner.login, pr.head.ref, pr.title.encode('ascii', errors='ignore'))
        if 'matching_files' in args:
            for f in args['matching_files']:
                print f


def _load_pr(**args):
    check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_pull(args['number'])


def _load_issue(**args):
    """Load the PR as an issue to enable actions like set_labels"""
    check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_issue(args['number'])


def _load_prs_by_branch(**args):
    check_required_fields(['token', 'repo', 'head'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    prs = [pr for pr in repo.get_pulls() if pr.head.ref == args['head'] and pr.base.ref == args['base']]
    if len(prs) is not 1:
        print "Probable error, found {0} pull(s) from {1} -> {2} (expected 1)".format(len(prs), args['head'], args['base'])
        _print_prs(prs, **args)
    return prs


def _validate_list_of_dict(list_of_dict):
    """
    Validates that obj is a list containing dictionaries with entries for 'pr' and 'issue'
    """
    return isinstance(list_of_dict, list) and 'pr' in list_of_dict[0] and 'issue' in list_of_dict[0]


def _return_specific_owner_prs(all_prs, filters):
    """
    Takes a list of dictionaries, containing a PR and its Issue Obj
    filters for an owner and returns filtered list of dictionaries
    """
    if _validate_list_of_dict(all_prs):
        return [pr for pr in all_prs if filters['owner'] == pr['pr'].user.login]
    else:
        return []


def _return_specific_labeled_prs(all_prs, filters):
    """
    Takes a list of dictionaries, containing a PR and its Issue Obj
    filters for a label and returns filtered list of dictionaries
    """
    if _validate_list_of_dict(all_prs):
        pr_issue = []
        for pull_request in all_prs:
            issue = pull_request['issue']
            labels = issue.get_labels()
            matched_labels = [label.name for label in labels if filters['label'] == label.name]
            if matched_labels:
                pr_issue.append({'pr':pull_request['pr'], 'issue':pull_request['issue']})
        return pr_issue
    else:
        return []


def _return_specific_status_prs(all_prs, filters):
    """
    Takes a list of dictionaries, containing a PR and its Issue Obj
    filters for status and returns filtered list of dictionaries
    """
    if _validate_list_of_dict(all_prs):
        pr_issue = []
        for pull_request in all_prs:
            commits = pull_request['pr'].get_commits()
            statuses = [[status.state] for status in commits.reversed[0].get_statuses() if filters['status'] == status.state]
            if statuses:
                pr_issue.append({'pr':pull_request['pr'], 'issue':pull_request['issue']})
        return pr_issue
    else:
        return []


def _return_specific_comment_prs(all_prs, filters):
    """
    Takes a list of dictionaries, containing a PR and its Issue Obj
    filters for comments and returns filtered list of dictionaries
    """
    if _validate_list_of_dict(all_prs):
        pr_issue = []
        for pull_request in all_prs:
            issue = pull_request['issue']
            comments = issue.get_comments()
            matched_comments = [comment.body for comment in comments if re.search(filters['comment'], comment.body)]
            if matched_comments:
                pr_issue.append({'pr':pull_request['pr'], 'issue':pull_request['issue']})
        return pr_issue
    else:
        return []


def _check_approved_mergers(approved_users, comment_users):
    comment_approved_users = [comment_user for comment_user in comment_users if comment_user in approved_users]
    if not comment_approved_users:
        raise NoApproversError("No approved mergers were found in comments - Approved mergers: %s " % approved_users)
    else:
        return comment_approved_users


def _check_approved_mergers_file(approved_mergers_file, comment_users):
    with open(approved_mergers_file) as approved_mergers_file:
        approved_users = approved_mergers_file.read().splitlines()
    return _check_approved_mergers(approved_users, comment_users)


def _check_owner_cannot_ship(owner, comment_users):
    matched_comment_non_owner_users = [comment_user for comment_user in comment_users if comment_user != owner]
    if not matched_comment_non_owner_users:
        raise OwnerCannotShipError("Owner cannot ship their own code - Owner: %s" % str(owner))
    else:
        return matched_comment_non_owner_users


def _merge_pr(pr, **args):
    if args['condition_approved_mergers'] or args['condition_use_approved_mergers_file'] or args['condition_non_owner_merger']:
        merge_comment_users = [comment.user.login for comment in _load_issue(**args).get_comments().reversed if re.search(".*%s.*" % args['mergecomment'], comment.body)]
        if args.get('condition_approved_mergers'):
            merge_comment_users = _check_approved_mergers(args['condition_approved_mergers'], merge_comment_users)
        if args.get('condition_use_approved_mergers_file'):
            merge_comment_users = _check_approved_mergers_file(args['approved_mergers_file_path'], merge_comment_users)
        if args.get('condition_non_owner_merger'):
            merge_comment_users = _check_owner_cannot_ship(pr.user.login, merge_comment_users)
        if merge_comment_users:
            pr.merge()
    else:
        pr.merge()


def github_check_condition(**args):
    tz_local = get_localzone()
    check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    pr = repo.get_pull(args['number'])
    issue = _load_issue(**args)
    last_commit_time = pytz.utc.localize(datetime.strptime(pr.get_commits().reversed[0].commit.raw_data['committer']['date'], '%Y-%m-%dT%H:%M:%SZ')).astimezone(tz_local)
    merge_comment_users = [comment.user.login for comment in issue.get_comments(since=last_commit_time).reversed if re.search('.*%s.*' % args['mergecomment'], comment.body) and comment.updated_at == comment.created_at]

    if not merge_comment_users:
        raise NoMergeCommentError("There are no merge comments associated with this PR")

    if args.get('condition_non_owner_merger'):
        merge_comment_users = _check_owner_cannot_ship(pr.user.login, merge_comment_users)
    if args.get('condition_use_approved_mergers_file'):
        merge_comment_users = _check_approved_mergers_file(args['approved_mergers_file_path'], merge_comment_users)
    if args.get('condition_approved_mergers'):
        merge_comment_users = _check_approved_mergers(args['condition_approved_mergers'], merge_comment_users)

    return merge_comment_users


def github_create_pr(**args):
    check_required_fields(['token', 'repo', 'title', 'body', 'base', 'head'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    pr = repo.create_pull(title=args['title'], body=args['body'], base=args['base'], head=args['head'])
    if 'label' in args and args['label']:
        args['number'] = pr.number
        github_add_labels(**args)
    _print_pr(pr, **args)


def github_list_prs(**args):
    check_required_fields(['token', 'repo'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    list_return_obj = None

    if 'number' in args and args['number']:
        pr = repo.get_pull(args['number'])
        if 'files' in args and args['files']:
            pr_files = pr.get_files()
            args['matching_files'] = [f.filename for f in pr_files]
        if 'comments' in args and args['comments']:
            pr = _load_issue(**args)
            list_return_obj = pr.get_comments()
        _print_prs([pr], **args)
    elif 'label' in args and args['label']:
        label_list = [repo.get_label(label) for label in args['label']]
        prs = [repo.get_pull(i.number) for i in repo.get_issues(labels=label_list) if i.pull_request]
        _print_prs(prs, **args)
    elif 'head' in args and args['head']:
        prs = _load_prs_by_branch(**args)
        _print_prs(prs, **args)
    elif 'filters' in args and args['filters']:
        prs = [pr['pr'] for pr in github_filter_prs(**args)]
        _print_prs(prs, **args)
    else:
        prs = repo.get_pulls()
        _print_prs(prs, **args)
    return list_return_obj


def github_filter_prs(**args):
    """
    Filters prs to return only what is contained in the filters
    Returns a list of dictionaries, containing a PR obj and its Issue obj
    """
    git_hub = Github(args['token'])
    repo = git_hub.get_repo(args['repo'])
    all_prs = [{'pr':repo.get_pull(pr.number), 'issue':repo.get_issue(pr.number)} for pr in repo.get_pulls()]
    filters = {}
    for filter_option in args['filters'].split(','):
        part = filter_option.partition("=")
        filters[part[0]] = part[2]

    if 'owner' in filters:
        all_prs = _return_specific_owner_prs(all_prs, filters)
    if 'label' in filters:
        all_prs = _return_specific_labeled_prs(all_prs, filters)
    if 'status' in filters:
        all_prs = _return_specific_status_prs(all_prs, filters)
    if 'comment' in filters:
        all_prs = _return_specific_comment_prs(all_prs, filters)

    return all_prs


def github_merge_pr_by_number(**args):
    check_required_fields(['token', 'repo', 'number'], **args)
    pr = _load_pr(**args)
    _merge_pr(pr, **args)


def github_merge_pr_by_branch(**args):
    check_required_fields(['token', 'repo', 'head'], **args)
    pr = _load_prs_by_branch(**args)[0]
    _merge_pr(pr, **args)


def github_comment_pr(**args):
    check_required_fields(['body'], **args)
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

    github-pr merge -r dataxu/test_repo -n 17 --condition-non-owner-merger --condition-approved-mergers-file=.approved-mergers-file
        This conditional option allows merges to go through checks that validate ownership and team hierarchy.
            ie.
                --condition-approved-mergers user1 user2 user3
                    This takes a SPACE-separated list, without quotes or braces
                or
                --condition-approved-mergers-file=.approved-mergers-file
        OPTIONAL: --mergecomment can be set to a different string to search for instead of ":shipit:"

Merge a PR by branch

    github-pr merge -r dataxu/test_repo --head dev-my-branch-name
    github-pr merge -r dataxu/test_repo --head dev-another-branch --base branch-that-is-not-master

Delete a PR

    github-pr delete -r dataxu/test_repo -n 17

Check conditional status checks
    !!!This check only looks at comments AFTER the latest commit, to validate that the
    most recent code (most recent git sha pushed to the PR) has been peer reviewed!!!

    github-pr check-condition -r dataxu/dcommand -n 84 --condition-non-owner-merger
        This will check to make sure that the owner can not apply a shipable comment on their own code
    github-pr check-condition -r dataxu/dcommand -n84 --condition-approved-mergers-file=<MAINTAINERS FILE>
        This takes the path to the MAINTAINERS file inside the repo
        Compares commenter to list from a file, single user per line, and checks to make sure they are an approved merger
    github-pr check-condition -r dataxu/dcommand -n 84 --condition-approved-mergers ned_flanders marge_simpson
        This takes a SPACE-separated list, without quotes or braces
        This will check that a comment containing a :shipit: (the default, or other defined comment if merge_comment is set)
        comes from a user in the provided list passed on the commandline. The "MAINTAINERS file" option above is the preferred
        convention to use, while this passing the list on the commandline option is primarily for local testing
        when setting up your CD flow.
        """)
    parser.add_argument('action', choices=['create', 'list', 'merge', 'comment', 'delete', 'update', 'check-condition'], help='action to take')
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
    parser.add_argument('--mergecomment', default=":shipit:", help='string to look for when checking comments for "shipit" approval, during MERGE only')
    parser.add_argument('--condition-non-owner-merger', action='store_true', help='stops owner from being able to apply merge comment')
    parser.add_argument('--condition-approved-mergers', default=None, nargs='+', help='list of usernames of approved mergers')
    parser.add_argument('--condition-approved-mergers-file', action='store_true', help='check a file for list of usernames of approved mergers')
    parser.add_argument('--approved-mergers-file-path', default='./MAINTAINERS.txt', help='location of file of usernames of approved mergers')

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

    elif 'action' in args and args['action'] == 'check-condition':
        github_check_condition(**args)

    gh = Github(args['token'])

    if (('numberonly' in args) and not args['numberonly']):
        if (('noratelimit' in args) and not args['noratelimit']):
            print "Github Rate Limiting: %d remaining of max %d" % (gh.rate_limiting[0], gh.rate_limiting[1])

if __name__ == '__main__':
    main()
