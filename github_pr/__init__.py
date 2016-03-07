#!/usr/bin/env python
import sys
import re
from tabulate import tabulate
from github import Github


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
    elif 'comments' in args and args['comments']:
        for comment in pr.get_comments():
            print "#%d : Comment - %s" % (pr.number, comment.body)
    else:
        print "#%d [%s] %10s <- %-30s    %s" % (pr.number, pr.state, pr.base.ref, pr.head.ref, pr.title.encode('ascii', errors='ignore'))
        if 'matching_files' in args:
            for f in args['matching_files']:
                print f


def _load_pr(**args):
    check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_pull(args['number'])


def _load_prs_by_branch(**args):
    check_required_fields(['token', 'repo', 'head'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    prs = [pr for pr in repo.get_pulls() if pr.head.ref == args['head'] and pr.base.ref == args['base']]
    if len(prs) is not 1:
        print "Probable error, found {0} pull(s) from {1} -> {2} (expected 1)".format(len(prs), args['head'], args['base'])
        _print_prs(prs, **args)
    return prs


def load_issue(**args):
    """Load the PR as an issue to enable actions like set_labels"""
    check_required_fields(['token', 'repo', 'number'], **args)
    gh = Github(args['token'])
    repo = gh.get_repo(args['repo'])
    return repo.get_issue(args['number'])


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
            pr = load_issue(**args)
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
    pr.merge()


def github_merge_pr_by_branch(**args):
    check_required_fields(['token', 'repo', 'head'], **args)
    pr = _load_prs_by_branch(**args)[0]
    pr.merge()


def github_comment_pr(**args):
    check_required_fields(['body'], **args)
    pr = _load_pr(**args)
    pr.create_issue_comment(args['body'])


def github_delete_pr(**args):
    pr = _load_pr(**args)
    pr.edit(state='closed')


def github_add_labels(**args):
    issue = load_issue(**args)
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
