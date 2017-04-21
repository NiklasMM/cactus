import sys

import click
from git import Repo

from cactuskeeper.git import (
    get_bugfixes_for_branch,
    get_commits_since_commit,
    get_latest_release_commit,
    get_release_branches,
)


@click.group()
@click.option('--repo', default=".", help="Path to the repository root")
@click.pass_context
def cli(context, repo):
    context.obj = {}
    context.obj["repo"] = repo


@cli.command()
@click.pass_context
def check(context):
    """
        Checks if the current branch of the repository is clean, i.e.
        no previous release branches contain fixes not present on this branch.
    """
    repo = Repo(context.obj["repo"])

    current_branch = repo.active_branch
    release_branches = get_release_branches(repo)

    branches_to_check = []
    for branch in reversed(release_branches):
        if current_branch == branch["branch"]:
            break
        else:
            branches_to_check.append(branch)

    fixes_on_base = set(get_bugfixes_for_branch(repo, current_branch).keys())

    clean = True
    for branch in branches_to_check:
        fixes = get_bugfixes_for_branch(
            repo, branch["branch"], current_branch
        )

        if len(set(fixes.keys()) - fixes_on_base) > 0:
            clean = False
            click.echo(
                "\nBranch '{other}' contains the following "
                "fixes not present in '{base}'".format(
                    base=current_branch, other=click.style(str(branch["branch"]), fg="yellow")
                )
            )

            for commit in fixes["_list"]:
                if commit.issue in fixes_on_base:
                    continue
                click.echo("\t({hexsha})\t{issue}\t{shortlog}".format(
                    shortlog=commit.shortlog, issue=commit.issue, hexsha=commit.object.hexsha[:11]
                ))
    if clean:
        click.echo("The current branch is clean")
    else:
        sys.exit(1)


@cli.command()
@click.option('--no-check', default=False, help="Omit integrity check before making the release")
@click.pass_context
def release(context, no_check):
    repo = Repo(context.obj["repo"])

    current_branch = repo.active_branch

    release = get_latest_release_commit(repo, current_branch)

    click.echo(
        "The last release on the branch is {0}.".format(click.style(release.version, fg="red"))
    )
    changelog_confirmed = False
    base_commit = release.object.hexsha

    while not changelog_confirmed:
        click.echo("This is the release log:")
        commits = get_commits_since_commit(repo, current_branch, base_commit)
        not_found = False

        # check if the specified base_commit is actually in the parents of the last found commit
        # otherwise we went until the end of the branch and did not find it
        if not any(c.hexsha.startswith(base_commit) for c in commits[-1].object.parents):
            click.echo("The specified commit was not found.")
            not_found = True
        else:
            for commit in commits:
                click.echo("\t{shortlog} {issue}".format(
                    shortlog=commit.shortlog, issue=commit.issue
                ))

        if not_found or click.confirm("Do you want to give a base commit manually?"):
            base_commit = click.prompt('Please enter the commit sha you want to use')
        else:
            changelog_confirmed = True
