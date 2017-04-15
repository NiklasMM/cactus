import re
from itertools import takewhile

RELEASE_BRANCHES = re.compile(r"release/v(?P<major>\d+)\.(?P<minor>\d+)")


def get_release_branches(repo, release_branch_re=RELEASE_BRANCHES):
    release_branches = []

    for branch in repo.branches:
        m = release_branch_re.match(str(branch))
        if m:
            release_branches.append(
                (branch, (int(m.group("major")), int(m.group("minor"))))
            )

    return sorted(release_branches, key=lambda x: x[1], reverse=True)


def get_bugfixes_for_branch(repo, branch, base_branch=None):
    if base_branch is not None:
        commits_on_branch = takewhile(
            lambda commit: commit not in repo.iter_commits(base_branch, max_count=100),
            repo.iter_commits(branch, max_count=10)
        )
    else:
        commits_on_branch = repo.iter_commits(branch)

    result = []
    for commit in commits_on_branch:
        if commit.message.startswith("release"):
            continue
        m = re.search("(#\d+)", commit.message)
        if m:
            result.append(m.group(0))
    return result
