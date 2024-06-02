from typing import Any

from actions_toolkit import core as actions_toolkit

from github.GithubException import GithubException
from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def __get_repo_secret_names__(repo: Repository, path: str = "actions") -> set[str]:
    if "admin:org" not in repo._requester.oauth_scopes and path == "dependabot":
        raise GithubException(403, None, None, "User token does not have access to dependabot secrets")
    if path in ["actions", "dependabot"]:
        return {secret.name for secret in repo.get_secrets(path)}
    else:
        return {secret.name for secret in repo.get_environment(path).get_secrets()}


def check_repo_secrets(repo: Repository, secrets: list[Secret]) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's secrets vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """
    repo_secret_names = set[str]()
    if any(filter(lambda secret: secret.type == "actions", secrets)):
        repo_secret_names.update(__get_repo_secret_names__(repo))
    if any(filter(lambda secret: secret.type == "dependabot", secrets)):
        repo_secret_names.update(__get_repo_secret_names__(repo, "dependabot"))
    if any(filter(lambda secret: secret.type not in {"actions", "dependabot"}, secrets)):
        first_secret = next(
            filter(lambda secret: secret.type not in {"actions", "dependabot"}, secrets),
            None,
        )
        if first_secret is not None:
            repo_secret_names.update(__get_repo_secret_names__(repo, first_secret.type))

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

    if len(diff["missing"]) + len(diff["extra"]) + len(diff["diff"]) > 0:
        return False, diff

    return True, None


def update_secrets(
    repo: Repository,
    secrets: list[Secret],
    diffs: tuple[dict[str, list[str] | dict[str, Any]]],
) -> set[str]:
    """Updates a repo's secrets to match the expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        set[str]: [description]
    """
    errors = []
    secret_dict = {secret.key: secret for secret in secrets}
    for issue_type in diffs.keys():
        for secret_name in diffs[issue_type]:
            try:
                if issue_type in ["missing", "diff"]:
                    if secret_dict[secret_name].type in ["actions", "dependabot"]:
                        repo.create_secret(
                            secret_name, secret_dict[secret_name].expected_value, secret_dict[secret_name].type
                        )
                    else:
                        repo.get_environment(secret_dict[secret_name].type).create_secret(
                            secret_name, secret_dict[secret_name].expected_value
                        )
                    # create_secret(repo, secret.key, secret.expected_value, secret.type)
                    actions_toolkit.info(f"Set {secret_name} to expected value")
                if issue_type == "extra":
                    if secret_dict[secret_name].type in ["actions", "dependabot"]:
                        repo.delete_secret(secret_name, secret_dict[secret_name].type)
                    else:
                        repo.get_environment(secret_dict[secret_name].type).delete_secret(secret_name)
                    # delete_secret(repo, secret.key, secret.type)
                    actions_toolkit.info(f"Deleted {secret_name}")
            except Exception as exc:  # this should be tighter
                if secret_dict[secret_name].required:
                    errors.append(
                        {
                            "type": "secret-update",
                            "key": secret_name,
                            "error": f"{exc}",
                        }
                    )
    return errors
