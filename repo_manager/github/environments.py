import json
from typing import Any

from actions_toolkit import core as actions_toolkit

from github.Repository import Repository

from repo_manager.schemas.environment import (
    environment,
    Reviewer,
    DeploymentBranchPolicy,
)

from .secrets import check_repo_secrets
from .secrets import update_secrets
from .variables import check_variables
from .variables import update_variables


def __get_environment_deployment_branch_policies(
    repo: Repository, environment: str
) -> set[str]:
    """:calls: `GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies
    <https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2022-11-28>`_

    :param repo: Repository
    """

    status, headers, raw_data = repo._requester.requestJson(
        "GET", f"{repo.url}/environments/{environment}/deployment-branch-policies"
    )
    if status != 200:
        raise Exception(
            f"Unable to list deployment branch policies for environment: {environment}. "
                + "Status: {status}. Error: {json.loads(raw_data)['message']}"
        )

    try:
        deployment_branch_policies_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise Exception(f"Github apu returned invalid json {exc}")

    return (
        {
            policy["name"]
            for policy in deployment_branch_policies_data["branch_policies"]
        }
        if deployment_branch_policies_data["branch_policies"]
        else set()
    )


def __create_environment_branch_policy(
    repo: Repository, environment_name: str, branch_name_pattern: str
) -> bool:
    """:calls: `PUT /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies
    <https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2022-11-28#create-or-update-a-branch-protection-policy>`_

    :param environment_name: string
    :rtype: bool
    """

    put_parameters = {"name": branch_name_pattern, "type": "branch"}
    status, headers, data = repo._requester.requestJson(
        "POST",
        f"{repo.url}/environments/{environment_name}/deployment-branch-policies",
        input=put_parameters,
    )
    if status not in {200}:
        raise Exception(
            f"Unable to create deployment branch policy for environment {environment_name} "
                + "with branch pattern {branch_name_pattern}. Status: {status}. Error: {json.loads(data)['message']}"
        )

    return True


def __delete_environment_branch_policy(
    repo: Repository, environment_name: str, branch_name_pattern: str
) -> bool:
    """:calls:
    `DELETE /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies/{branch_name_pattern}
    <https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2022-11-28#delete-a-branch-protection-policy>`_

    :param environment_name: string
    :rtype: bool
    """
    status, headers, raw_data = repo._requester.requestJson(
        "GET", f"{repo.url}/environments/{environment_name}/deployment-branch-policies"
    )
    if status != 200:
        raise Exception(
            f"Unable to list deployment branch policies for environment: {environment_name}. "
                + "Status: {status}. Error: {json.loads(raw_data)['message']}"
        )

    try:
        deployment_branch_policies_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise Exception(f"Github apu returned invalid json {exc}")

    branch_policy_id = [
        branch_policy["id"]
        for branch_policy in filter(
            lambda branch_policy: branch_policy["name"] == branch_name_pattern,
            deployment_branch_policies_data["branch_policies"],
        )
    ][0]

    status, headers, data = repo._requester.requestJson(
        "DELETE",
        f"{repo.url}/environments/{environment_name}/deployment-branch-policies/{branch_policy_id}",
    )
    if status not in {204}:
        raise Exception(
            f"Unable to delete deployment branch policy for environment {environment_name} "
                + "with branch policy id {branch_policy_id}. Status: {status}. Error: {json.loads(data)['message']}"
        )

    return True


def delete_environment(repo: Repository, environment_name: str) -> bool:
    """:calls: `DELETE /repos/{owner}/{repo}/environments/{environment_name}
        <https://docs.github.com/en/rest/deployments/environments?apiVersion=2022-11-28#delete-an-environment>`_
    :param environment_name: string
    :rtype: bool
    """
    status, headers, data = repo._requester.requestJson(
        "DELETE", f"{repo.url}/environments/{environment_name}"
    )
    return status == 204


def diff_option(key: str, expected: Any, repo_value: Any) -> str | None:
    if expected != repo_value:
        return f"{key} -- Expected: {expected} Found: {repo_value}"
    return None


def create_environment(repo: Repository, env: environment) -> bool:
    """:calls: `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}
    <https://docs.github.com/en/rest/deployments/environments?apiVersion=2022-11-28#create-or-update-an-environment>`_

    :param environment_name: string
    :rtype: bool
    """
    put_parameters = {
        # "prevent_self_review": env.prevent_self_review, # GitHub docs list this, but error says it is invalid...
        "reviewers": (
            [{"type": reviewer.type, "id": reviewer.id} for reviewer in env.reviewers]
            if len(env.reviewers) > 0
            else None
        ),
        "deployment_branch_policy": (
            {
                "protected_branches": env.deployment_branch_policy.protected_branches,
                "custom_branch_policies": env.deployment_branch_policy.custom_branch_policies,
            }
            if env.deployment_branch_policy is not None
            else None
        ),
    }
    if env.wait_timer is not None:
        put_parameters["wait_timer"] = env.wait_timer
    status, headers, data = repo._requester.requestJson(
        "PUT", f"{repo.url}/environments/{env.name}", input=put_parameters
    )
    if status not in {200}:
        raise Exception(
            f"Unable to create environment: {env.name}. Status: {status}. Error: {json.loads(data)['message']}"
        )

    return True


def check_environment_settings(
    repo: Repository, config_env: environment
) -> tuple[bool, dict[str, Any]]:
    repo_env = repo.get_environment(config_env.name)
    repo_protection_rules_dict = {
        protection_rule.type: protection_rule
        for protection_rule in repo_env.protection_rules
    }
    diffs = {
        "wait_timer": None,
        "branch_policy": {},
        "required_reviewers": {},
    }
    keys = {
        "wait_timer",
        "branch_policy",
        "required_reviewers",
    }  # can't use keys() because it's changes during iterator
    for protection_rule in keys:
        if protection_rule == "required_reviewers":
            config_reviewers = {
                reviewer.name: reviewer for reviewer in config_env.reviewers
            }
            repo_reviewers = repo_protection_rules_dict.get("required_reviewers", None)
            if repo_reviewers is None:
                repo_reviewers = {}
            else:
                repo_reviewers = {
                    reviewer.reviewer.login: Reviewer(
                        type=reviewer.type, name=reviewer.reviewer.login
                    )
                    for reviewer in repo_reviewers.reviewers
                }
            if len(config_reviewers.keys() - repo_reviewers.keys()) > 0:
                diffs[protection_rule]["missing"] = [
                    config_reviewers.keys() - repo_reviewers.keys()
                ]
            if len(repo_reviewers.keys() - config_reviewers.keys()) > 0:
                diffs[protection_rule]["extra"] = [
                    repo_reviewers.keys() - config_reviewers.keys()
                ]
            diff_reviewers = {}
            reviewers_to_check_values_on = list(
                config_reviewers.keys() & repo_reviewers.keys()
            )
            for reviewer_name in reviewers_to_check_values_on:
                if (
                    config_reviewers[reviewer_name].type
                    != repo_reviewers[reviewer_name].type
                ):
                    diff_reviewers[reviewer_name] = diff_option(
                        reviewer_name,
                        config_reviewers[reviewer_name].type,
                        repo_reviewers[reviewer_name].type,
                    )
            if len(diff_reviewers) > 0:
                diffs[protection_rule]["diff"] = diff_reviewers
        elif protection_rule == "branch_policy":
            config_value = config_env.deployment_branch_policy
            repo_value = (
                DeploymentBranchPolicy(
                    protected_branches=repo_env.deployment_branch_policy.protected_branches,
                    custom_branch_policies=repo_env.deployment_branch_policy.custom_branch_policies,
                )
                if repo_env.deployment_branch_policy is not None
                else None
            )
            if config_value != repo_value:
                diffs[protection_rule]["rules"] = diff_option(
                    protection_rule, config_value, repo_value
                )
        else:
            config_value = getattr(config_env, protection_rule)
            repo_value = getattr(
                repo_protection_rules_dict.get(protection_rule, None), protection_rule
            )
            if config_value != repo_value:
                diffs[protection_rule] = diff_option(
                    protection_rule, config_value, repo_value
                )

        if diffs[protection_rule] is None or len(diffs[protection_rule]) == 0:
            diffs.pop(protection_rule)

    if len(diffs) > 0:
        return False, diffs

    return True, None


def check_branch_policies(
    repo: Repository, env: environment
) -> tuple[bool, dict[str, Any]]:
    if (
        env.deployment_branch_policy is not None
        and env.deployment_branch_policy.custom_branch_policies
    ):
        branch_patterns = {}
        repo_branch_name_patterns = __get_environment_deployment_branch_policies(
            repo, env.name
        )
        config_branch_name_patterns = env.branch_name_patterns
        if config_branch_name_patterns != repo_branch_name_patterns:
            missing_patterns = list(
                config_branch_name_patterns - repo_branch_name_patterns
            )
            if len(missing_patterns) > 0:
                branch_patterns["missing"] = missing_patterns
            extra_patterns = list(
                repo_branch_name_patterns - config_branch_name_patterns
            )
            if len(extra_patterns) > 0:
                branch_patterns["extra"] = extra_patterns
        if len(branch_patterns) > 0:
            return False, branch_patterns
    else:
        return True, None


def check_repo_environments(
    repo: Repository, environments: list[environment]
) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's environments vs our expected settings

    Args:
        repo (Repository): [description]
        environments (List[Environment]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """

    repo_environments = repo.get_environments()
    repo_environment_names = {environment.name for environment in repo_environments}

    expected_environment_names = {
        environment.name
        for environment in filter(lambda environment: environment.exists, environments)
    }
    diff = {}
    if len(expected_environment_names - repo_environment_names) > 0:
        diff["missing"] = list(expected_environment_names - repo_environment_names)
    if len(repo_environment_names - expected_environment_names) > 0:
        diff["extra"] = list(
            repo_environment_names.intersection(
                {
                    environment.name
                    for environment in filter(
                        lambda environment: environment.exists is False, environments
                    )
                }
            )
        )

    environments_to_check_values_on = list(
        expected_environment_names.intersection(repo_environment_names)
    )
    config_env_dict = {environment.name: environment for environment in environments}
    env_diffs = {}
    for env_name in environments_to_check_values_on:
        config_env = config_env_dict.get(env_name, None)
        diffs_by_env = {}
        check_result = True
        for check, to_check in {
            check_environment_settings: ("settings", config_env),
            check_branch_policies: ("branch_policies", config_env),
            check_repo_secrets: ("secrets", config_env.secrets),
            check_variables: ("variables", config_env.variables),
        }.items():
            check_name, to_check = to_check
            if to_check is not None:
                this_check, this_diffs = check(repo, to_check)
                check_result &= this_check
                if this_diffs is not None:
                    diffs_by_env[check_name] = this_diffs

        if len(diffs_by_env) > 0:
            env_diffs[env_name] = diffs_by_env

    if len(env_diffs) > 0:
        diff["diff"] = env_diffs

    if len(diff) > 0:
        return False, diff

    return True, None


def update_environments(
    repo: Repository, environments: list[environment], diffs: dict[str, Any]
) -> set[str]:
    """Updates a repo's environments to match the expected settings

    Args:
        repo (Repository): [description]
        environments (List[environment]): [description]
        diffs (Dictionary[string, Any]): List of all the summarized differences by environment name

    Returns:
        set[str]: [description]
    """
    errors = []
    config_env_dict = {environment.name: environment for environment in environments}
    try:
        for issue_type in diffs.keys():
            for env_name in diffs[issue_type].keys():
                if issue_type == "missing":
                    components = {"settings", "branch_policies", "secrets", "variables"}
                elif issue_type == "extra":
                    components = {}
                else:
                    components = diffs[issue_type][env_name].keys()
                for env_component in components:
                    pErrors = []
                    if env_component == "settings":
                        create_environment(repo, config_env_dict[env_name])
                    if env_component == "branch_policies":
                        if issue_type == "missing":
                            branch_policy_issue_types = {issue_type}
                        else:
                            branch_policy_issue_types = diffs[issue_type][env_name][
                                env_component
                            ].keys()
                        for branch_policy_issue_type in branch_policy_issue_types:
                            if branch_policy_issue_type == "missing":
                                for branch_name_pattern in diffs[issue_type][env_name][
                                    env_component
                                ][branch_policy_issue_type]:
                                    pErrors.append(
                                        f"Unable to link deployment environment {env_name} "
                                            + f"to branches {branch_name_pattern}. "
                                            + "Currently the GitHub API does not support "
                                            + "creating branch policies for environments; get error 404..."
                                    )
                                    # __create_environment_branch_policy(repo, env_name, branch_name_pattern)
                            if branch_policy_issue_type == "extra":
                                for branch_name_pattern in diffs[issue_type][env_name][
                                    env_component
                                ][branch_policy_issue_type]:
                                    __delete_environment_branch_policy(
                                        repo, env_name, branch_name_pattern
                                    )
                    elif (
                        env_component == "secrets"
                        and config_env_dict[env_name].secrets is not None
                    ):
                        pErrors = update_secrets(
                            repo, config_env_dict[env_name].secrets
                        )
                    elif (
                        env_component == "variables"
                        and config_env_dict[env_name].variables is not None
                    ):
                        if issue_type == "missing":
                            diffs[issue_type][env_name][env_component] = {
                                "missing": [
                                    variable.key
                                    for variable in config_env_dict[env_name].variables
                                ]
                            }
                        pErrors = update_variables(
                            repo,
                            config_env_dict[env_name].variables,
                            diffs[issue_type][env_name][env_component],
                        )
                    if len(pErrors) > 0:
                        errors.append(pErrors)
                    else:
                        actions_toolkit.info(
                            f"Synced {env_component} for environment {env_name}"
                        )
            if issue_type == "extra":
                if delete_environment(repo, env_name):
                    actions_toolkit.info(f"Deleted {environment.name}")
    except Exception as exc:
        errors.append({"type": f"{env_component}-update", "error": f"{exc}"})
    return errors
