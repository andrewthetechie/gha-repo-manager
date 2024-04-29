import json
from typing import Any

from actions_toolkit import core as actions_toolkit

from github.PublicKey import PublicKey
from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def get_public_key(repo: Repository, secret_type: str = "actions") -> PublicKey:
    """
    :calls: `GET /repos/{owner}/{repo}/actions/secrets/public-key
    <https://docs.github.com/en/rest/reference/actions#get-a-repository-public-key>`_
    :rtype: :class:`github.PublicKey.PublicKey`
    """
    # can only access dependabot secrets with admin:org scope
    # https://docs.github.com/en/rest/dependabot/secrets?apiVersion=2022-11-28
    if "admin:org" not in repo._requester.oauth_scopes and secret_type == "dependabot":
        raise Exception(
            "dependabot secrets require admin:org scope for the token used to access them."
        )
    headers, data = repo._requester.requestJsonAndCheck(
        "GET", f"{repo.url}/{secret_type}/secrets/public-key"
    )
    return PublicKey(repo._requester, headers, data, completed=True)


def create_secret(
    repo: Repository,
    secret_name: str,
    unencrypted_value: str,
    secret_type: str = "actions",
) -> bool:
    """
    :calls: `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}
    <https://docs.github.com/en/rest/reference/actions#get-a-repository-secret>`_

    Copied from https://github.com/PyGithub/PyGithub/blob/master/github/Repository.py#L1428 in order to
    support dependabot
    :param secret_name: string
    :param unencrypted_value: string
    :rtype: bool
    """
    public_key = get_public_key(repo, secret_type)
    payload = public_key.encrypt(unencrypted_value)
    put_parameters = {
        "key_id": public_key.key_id,
        "encrypted_value": payload,
    }
    # can only access dependabot secrets with admin:org scope
    # https://docs.github.com/en/rest/dependabot/secrets?apiVersion=2022-11-28
    if "admin:org" not in repo._requester.oauth_scopes and secret_type == "dependabot":
        raise Exception(
            "dependabot secrets require admin:org scope for the token used to access them."
        )
    status, headers, data = repo._requester.requestJson(
        "PUT", f"{repo.url}/{secret_type}/secrets/{secret_name}", input=put_parameters
    )
    if status not in (201, 204):
        raise Exception(f"Unable to create {secret_type} secret. Status code: {status}")
    return True


def delete_secret(
    repo: Repository, secret_name: str, secret_type: str = "actions"
) -> bool:
    """
    Copied from https://github.com/PyGithub/PyGithub/blob/master/github/Repository.py#L1448
    to add support for dependabot
    :calls: `DELETE /repos/{owner}/{repo}/actions/secrets/{secret_name}
        <https://docs.github.com/en/rest/reference/actions#delete-a-repository-secret>`_
    :param secret_name: string
    :rtype: bool
    """
    # can only access dependabot secrets with admin:org scope
    # https://docs.github.com/en/rest/dependabot/secrets?apiVersion=2022-11-28
    if "admin:org" not in repo._requester.oauth_scopes and secret_type == "dependabot":
        raise Exception(
            "dependabot secrets require admin:org scope for the token used to access them."
        )
    status, headers, data = repo._requester.requestJson(
        "DELETE", f"{repo.url}/{secret_type}/secrets/{secret_name}"
    )
    return status == 204


def check_repo_secrets(
    repo: Repository, secrets: list[Secret]
) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
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
    if any(
        filter(lambda secret: secret.type not in {"actions", "dependabot"}, secrets)
    ):
        first_secret = next(
            filter(
                lambda secret: secret.type not in {"actions", "dependabot"}, secrets
            ),
            None,
        )
        if first_secret is not None:
            repo_secret_names.update(_get_repo_secret_names(repo, first_secret.type))

    expected_secrets_names = {
        secret.key for secret in filter(lambda secret: secret.exists, secrets)
    }
    diff = {
        "missing": list(expected_secrets_names - repo_secret_names),
        "extra": repo_secret_names.intersection(
            {
                secret.key
                for secret in filter(lambda secret: secret.exists is False, secrets)
            }
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
    status, headers, raw_data = repo._requester.requestJson(
        "GET", f"{repo.url}/{type}/secrets"
    )
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
                create_secret(repo, secret.key, secret.expected_value, secret.type)
                actions_toolkit.info(f"Set {secret.key} to expected value")
            except Exception as exc:  # this should be tighter
                errors.append(
                    {
                        "type": "secret-update",
                        "key": secret.key,
                        "error": f"{exc}",
                    }
                )
        else:
            try:
                delete_secret(repo, secret.key, secret.type)
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
