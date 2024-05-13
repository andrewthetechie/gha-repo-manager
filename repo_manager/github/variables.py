import json
from typing import Any

from actions_toolkit import core as actions_toolkit

from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def diff_option(key: str, expected: Any, repo_value: Any) -> str | None:
    if expected is not None:
        if expected != repo_value:
            return f"{key} -- Expected: {expected} Found: {repo_value}"
    return None


def _get_repo_variables(repo: Repository, path: str = "actions") -> Any:
    status, headers, raw_data = repo._requester.requestJson(
        "GET", f"{repo.url}/{path}/variables"
    )
    if status != 200:
        raise Exception(
            f"Unable to get repo's variables. Status: {status}. Error: {json.loads(raw_data)['message']}"
        )
    try:
        variable_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise Exception(f"Github apu returned invalid json {exc}")

    return variable_data["variables"]


def _get_repo_variable_names(repo: Repository, path: str = "actions") -> set[str]:
    return {variable["name"] for variable in _get_repo_variables(repo, path)}


def _get_repo_variable_dict(repo: Repository, path: str = "actions") -> dict[str, Any]:
    return {variable["name"]: variable for variable in _get_repo_variables(repo, path)}


def create_variable(
    repo: Repository, variable_name: str, value: str, path: str = "actions"
) -> bool:
    """
    :calls: `POST /repos/{owner}/{repo}/{path}/variables
    <https://docs.github.com/en/rest/actions/variables?apiVersion=2022-11-28>`_

    :param variable_name: string
    :param value: string
    :path: string
    """
    put_parameters = {"name": variable_name, "value": value}
    status, headers, data = repo._requester.requestJson(
        "POST", f"{repo.url}/{path}/variables", input=put_parameters
    )
    if status not in {201}:
        raise Exception(
            f"Unable to create variable: {variable_name}. Error: {json.loads(data)['message']}"
        )
    return True


def update_variable(
    repo: Repository, variable_name: str, value: str, path: str = "actions"
) -> bool:
    """
    :calls: `PATCH /repos/{owner}/{repo}/{path}/variables/{variable_name}
    <https://docs.github.com/en/rest/actions/variables?apiVersion=2022-11-28>`_

    :param variable_name: string
    :param value: string
    :path: string
    """
    put_parameters = {"name": variable_name, "value": value}
    status, headers, data = repo._requester.requestJson(
        "PATCH", f"{repo.url}/{path}/variables/{variable_name}", input=put_parameters
    )
    if status not in {204}:
        raise Exception(
            f"Unable to update variable: {variable_name}. Error: {json.loads(data)['message']}"
        )
    return True


def delete_variable(
    repo: Repository, variable_name: str, path: str = "actions"
) -> bool:
    """
    :calls: `DELETE /repos/{owner}/{repo}/{path}/variables/{variable_name}
    <https://docs.github.com/en/rest/actions/variables?apiVersion=2022-11-28>`_

    :param variable_name: string
    :path: string
    """
    status, headers, data = repo._requester.requestJson(
        "DELETE", f"{repo.url}/{path}/variables/{variable_name}"
    )
    if status not in {204}:
        raise Exception(
            f"Unable to delete variable: {variable_name}. Error: {json.loads(data)['message']}"
        )
    return status == 204


def check_variables(
    repo: Repository, variables: list[Secret]
) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's secrets vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """
    repo_dict = dict[str, Any]()
    if any(filter(lambda variable: variable.type == "actions", variables)):
        repo_dict.update(_get_repo_variable_dict(repo))
    if any(filter(lambda variable: variable.type not in {"actions"}, variables)):
        first_variable = next(
            filter(lambda variable: variable.type not in {"actions"}, variables), None
        )
        if first_variable is not None:
            repo_dict.update(_get_repo_variable_dict(repo, first_variable.type))
    config_dict = {variable.key: variable for variable in variables}
    repo_variable_names = {variable for variable in repo_dict.keys()}

    expected_variables_names = {
        variable.key for variable in filter(lambda variable: variable.exists, variables)
    }
    diff = {
        "missing": list(expected_variables_names - repo_variable_names),
        "extra": list(
            repo_variable_names.intersection(
                {
                    variable.key
                    for variable in filter(
                        lambda variable: variable.exists is False, variables
                    )
                }
            )
        ),
        "diff": {},
    }

    variables_to_check_values_on = list(
        expected_variables_names.intersection(repo_variable_names)
    )
    for variable_name in variables_to_check_values_on:
        config_var = config_dict.get(variable_name, None)
        repo_var = repo_dict.get(variable_name, None)
        if config_var.value != repo_var["value"]:
            diff["diff"][variable_name] = diff_option(
                variable_name, config_var.value, repo_var["value"]
            )

    if len(diff["missing"]) + len(diff["extra"]) + len(diff["diff"]) > 0:
        return False, diff

    return True, None


def update_variables(
    repo: Repository,
    variables: list[Secret],
    diffs: tuple[dict[str, list[str] | dict[str, Any]]],
) -> set[str]:
    """Updates a repo's secrets to match the expected settings

    Args:
        repo (Repository): [description]
        variables (List[Secret]): [description]

    Returns:
        set[str]: [description]
    """
    errors = []
    variables_dict = {variable.key: variable for variable in variables}
    for variable in diffs["missing"]:
        try:
            create_variable(
                repo,
                variable,
                variables_dict[variable].value,
                variables_dict[variable].type,
            )
            actions_toolkit.info(f"Created variable {variable}")
        except Exception as exc:  # this should be tighter
            errors.append(
                {
                    "type": "variable-update",
                    "key": variable.key,
                    "error": f"{exc}",
                }
            )
    for variable in diffs["diff"].keys():
        try:
            update_variable(
                repo,
                variable,
                variables_dict[variable].value,
                variables_dict[variable].type,
            )
            actions_toolkit.info(f"Set variable {variable} to expected value")
        except Exception as exc:  # this should be tighter
            errors.append(
                {
                    "type": "variable-update",
                    "key": variable.key,
                    "error": f"{exc}",
                }
            )
    for variable in diffs["extra"]:
        try:
            delete_variable(repo, variable, variables_dict[variable].type)
            actions_toolkit.info(f"Deleted variable {variable}")
        except Exception as exc:  # this should be tighter
            errors.append(
                {
                    "type": "variable-update",
                    "key": variable.key,
                    "error": f"{exc}",
                }
            )
    return errors
