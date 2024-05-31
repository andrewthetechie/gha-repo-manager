from typing import Any
from actions_toolkit import core as actions_toolkit

from github.Repository import Repository

from repo_manager.utils import get_organization
from repo_manager.schemas.collaborator import Collaborator


def diff_option(key: str, expected: Any, repo_value: Any) -> str | None:
    if expected is not None:
        if expected != repo_value:
            return f"{key} -- Expected: {expected} Found: {repo_value}"
    return None


def check_collaborators(
    repo: Repository, collaborators: list[Collaborator]
) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's environments vs our expected settings

    Args:
        repo (Repository): [description]
        environments (List[Environment]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """

    diff = {}

    expected_collab_usernames = {
        collaborator.name
        for collaborator in filter(
            lambda collaborator: collaborator.type == "User" and collaborator.exists,
            collaborators,
        )
    }
    expected_collab_teamnames = {
        collaborator.name
        for collaborator in filter(
            lambda collaborator: collaborator.type == "Team" and collaborator.exists,
            collaborators,
        )
    }
    repo_collab_users = repo.get_collaborators()
    repo_collab_teams = repo.get_teams()  # __get_teams__(repo)
    repo_collab_usernames = {collaborator.login for collaborator in repo_collab_users}
    repo_collab_teamnames = {collaborator.slug for collaborator in repo_collab_teams}

    missing_users = list(expected_collab_usernames - repo_collab_usernames)
    missing_teams = list(expected_collab_teamnames - repo_collab_teamnames)
    if len(missing_users) + len(missing_teams) > 0:
        diff["missing"] = {}
        if len(missing_users) > 0:
            diff["missing"]["Users"] = missing_users
        if len(missing_teams) > 0:
            diff["missing"]["Teams"] = missing_teams

    extra_users = list(
        repo_collab_usernames.intersection(
            collaborator.name
            for collaborator in filter(
                lambda collaborator: collaborator.type == "User" and not collaborator.exists,
                collaborators,
            )
        )
    )
    extra_teams = list(
        repo_collab_teamnames.intersection(
            collaborator.name
            for collaborator in filter(
                lambda collaborator: collaborator.type == "Team" and not collaborator.exists,
                collaborators,
            )
        )
    )
    if len(extra_users) + len(extra_teams) > 0:
        diff["extra"] = {}
        if len(extra_users) > 0:
            diff["extra"]["Users"] = extra_users
        if len(extra_teams) > 0:
            diff["extra"]["Teams"] = extra_teams

    collaborators_to_check_values_on = {}
    collaborators_to_check_values_on["Users"] = list(expected_collab_usernames.intersection(repo_collab_usernames))
    collaborators_to_check_values_on["Teams"] = list(expected_collab_teamnames.intersection(repo_collab_teamnames))
    config_collaborator_dict = {collaborator.name: collaborator for collaborator in collaborators}
    repo_collab_dict = {"Users": {}, "Teams": {}}
    repo_collab_dict["Users"] = {collaborator.login: collaborator for collaborator in repo_collab_users}
    repo_collab_dict["Teams"] = {collaborator.slug: collaborator for collaborator in repo_collab_teams}
    perm_diffs = {"Users": {}, "Teams": {}}
    for collaborator_type in collaborators_to_check_values_on.keys():
        for collaborator_name in collaborators_to_check_values_on[collaborator_type]:
            if collaborator_type == "Users":
                repo_value = getattr(
                    repo_collab_dict[collaborator_type][collaborator_name].permissions,
                    config_collaborator_dict[collaborator_name].permission,
                    None,
                )
            else:
                repo_value = (
                    getattr(
                        repo_collab_dict[collaborator_type][collaborator_name],
                        "permission",
                        None,
                    )
                    == config_collaborator_dict[collaborator_name].permission
                )
            if repo_value is not True:
                perm_diffs[collaborator_type][collaborator_name] = diff_option(
                    config_collaborator_dict[collaborator_name].permission,
                    True,
                    repo_value,
                )

    if len(perm_diffs["Users"]) == 0:
        perm_diffs.pop("Users")

    if len(perm_diffs["Teams"]) == 0:
        perm_diffs.pop("Teams")

    if len(perm_diffs) > 0:
        diff["diff"] = perm_diffs

    if len(diff) > 0:
        return False, diff

    return True, None


def update_collaborators(repo: Repository, collaborators: list[Collaborator], diffs: dict[str, Any]) -> set[str]:
    """Updates a repo's environments to match the expected settings

    Args:
        repo (Repository): [description]
        environments (List[environment]): [description]
        diffs (Dictionary[string, Any]): List of all the summarized differences by environment name

    Returns:
        set[str]: [description]
    """
    errors = []
    users_dict = {
        collaborator.name: collaborator
        for collaborator in filter(
            lambda collaborator: collaborator.type == "User" and collaborator.name,
            collaborators,
        )
    }
    teams_dict = {
        collaborator.name: collaborator
        for collaborator in filter(
            lambda collaborator: collaborator.type == "Team" and collaborator.name,
            collaborators,
        )
    }

    def switch(collaborator: Collaborator, diff_type: str) -> None:
        if diff_type == "missing":
            if collaborator.type == "User":
                repo.add_to_collaborators(collaborator.name, collaborator.permission)
            elif collaborator.type == "Team":
                get_organization().get_team_by_slug(collaborator.name).update_team_repository(
                    repo, collaborator.permission
                )
            actions_toolkit.info(f"Added collaborator {collaborator.name} with permission {collaborator.permission}.")
        elif diff_type == "extra":
            if collaborator.type == "User":
                repo.remove_from_collaborators(collaborator.name)
            elif collaborator.type == "Team":
                get_organization().get_team_by_slug(collaborator.name).remove_from_repos(repo)
            else:
                raise Exception(f"Modifying collaborators of type {collaborator.type} not currently supported")
            actions_toolkit.info(f"Removed collaborator {collaborator.name}.")
        elif diff_type == "diff":
            if collaborator.type == "User":
                repo.add_to_collaborators(collaborator.name, collaborator.permission)
            elif collaborator.type == "Team":
                get_organization().get_team_by_slug(collaborator.name).update_team_repository(
                    repo, collaborator.permission
                )
            else:
                raise Exception(f"Modifying collaborators of type {collaborator.type} not currently supported")
            actions_toolkit.info(f"Updated collaborator {collaborator.name} with permission {collaborator.permission}.")
        else:
            errors.append(f"Collaborator {collaborator} not found in expected collaborators")

    for diff_type in diffs.keys():
        for collaborator_type in diffs[diff_type]:
            for collaborator in diffs[diff_type][collaborator_type]:
                if collaborator_type == "Users":
                    switch(users_dict[collaborator], diff_type)
                elif collaborator_type == "Teams":
                    switch(teams_dict[collaborator], diff_type)
                else:
                    raise Exception(f"Modifying collaborators of type {collaborator_type} not currently supported")

    return errors
