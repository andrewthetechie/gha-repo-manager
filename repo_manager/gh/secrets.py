import json
from typing import Any

from actions_toolkit import core as actions_toolkit

from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def check_repo_secrets(repo: Repository, secrets: list[Secret]) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's secrets vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """
    checked = True
    repo_secret_names = set[str]()
    if any(filter(lambda secret: secret.type == "actions", secrets)):
        repo_secret_names.update(_get_repo_secret_names(repo))
    if any(filter(lambda secret: secret.type == "dependabot", secrets)):
        repo_secret_names.update(_get_repo_secret_names(repo, "dependabot"))
    if any(filter(lambda secret: secret.type not in {"actions", "dependabot"}, secrets)):
        first_secret = next(
            filter(lambda secret: secret.type not in {"actions", "dependabot"}, secrets),
            None,
        )
        if first_secret is not None:
            repo_secret_names.update(_get_repo_secret_names(repo, first_secret.type))

    expected_secrets_names = {secret.key for secret in filter(lambda secret: secret.exists, secrets)}
    diff = {
        "missing": list(expected_secrets_names - repo_secret_names),
        "extra": repo_secret_names.intersection(
            {secret.key for secret in filter(lambda secret: secret.exists is False, secrets)}
        ),
        # Because we cannot diff secret values, we assume they are different if they exist
        "diff": repo_secret_names.intersection(
            {secret.key for secret in filter(lambda secret: secret.exists, secrets)}
        ),
    }

    if len(diff["missing"]) + len(diff["extra"]) > 0:
        checked = False

    return checked, diff


def _get_repo_secret_names(repo: Repository, type: str = "actions") -> set[str]:
    if "admin:org" not in repo._requester.oauth_scopes and type == "dependabot":
        return set()
    status, headers, raw_data = repo._requester.requestJson("GET", f"{repo.url}/{type}/secrets")
    if status != 200:
        raise Exception(f"Unable to get repo's secrets {status}")
    try:
        secret_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise Exception(f"Github apu returned invalid json {exc}")

    return {secret["name"] for secret in secret_data["secrets"]}


def update_secrets(repo: Repository, secrets: list[Secret]) -> set[str]:
    """Updates a repo's secrets to match the expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        set[str]: [description]
    """
    errors = []
    for secret in secrets:
        # Because we cannot diff secrets, just apply it every time
        if secret.exists:
            try:
                if secret.type in ["actions", "dependabot"]:
                    repo.create_secret(secret.key, secret.expected_value, secret.type)
                else:
                    repo.get_environment(secret.type).create_secret(secret.key, secret.expected_value)
                # create_secret(repo, secret.key, secret.expected_value, secret.type)
                actions_toolkit.info(f"Set {secret.key} to expected value")
            except Exception as exc:  # this should be tighter
                if secret.required:
                    errors.append(
                        {
                            "type": "secret-update",
                            "key": secret.key,
                            "error": f"{exc}",
                        }
                    )
        else:
            try:
                if secret.type in ["actions", "dependabot"]:
                    repo.delete_secret(secret.key, secret.type)
                else:
                    repo.get_environment(secret.type).delete_secret(secret.key)
                # delete_secret(repo, secret.key, secret.type)
                actions_toolkit.info(f"Deleted {secret.key}")
            except Exception as exc:  # this should be tighter
                errors.append(
                    {
                        "type": "secret-delete",
                        "key": secret.key,
                        "error": f"{exc}",
                    }
                )
    return errors
