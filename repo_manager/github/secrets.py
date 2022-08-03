import json
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def create_secret(repo: Repository, secret_name: str, unencrypted_value: str, is_dependabot: bool = False) -> bool:
    """
    :calls: `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name} <https://docs.github.com/en/rest/reference/actions#get-a-repository-secret>`_

    Copied from https://github.com/PyGithub/PyGithub/blob/master/github/Repository.py#L1428 in order to support dependabot
    :param secret_name: string
    :param unencrypted_value: string
    :rtype: bool
    """
    public_key = repo.get_public_key()
    payload = public_key.encrypt(unencrypted_value)
    put_parameters = {
        "key_id": public_key.key_id,
        "encrypted_value": payload,
    }
    secret_type = "actions" if not is_dependabot else "dependabot"
    status, headers, data = repo._requester.requestJson(
        "PUT", f"{repo.url}/actions/{secret_type}/{secret_name}", input=put_parameters
    )
    return status == 201


def check_repo_secrets(
    repo: Repository, secrets: List[Secret]
) -> Tuple[bool, Dict[str, Union[List[str], Dict[str, Any]]]]:
    """Checks a repo's secrets vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    Returns:
        Tuple[bool, Optional[List[str]]]: [description]
    """
    status, headers, raw_data = repo._requester.requestJson("GET", f"{repo.url}/actions/secrets")
    if status != 200:
        raise Exception(f"Unable to get repo's secrets {status}")
    try:
        secret_data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise Exception(f"Github apu returned invalid json {exc}")

    checked = True

    repo_secret_names = [secret["name"] for secret in secret_data["secrets"]]
    secrets_dict = {secret.key: secret for secret in secrets}
    expected_secret_names = [secret.key for secret in secrets if secret.exists]
    diff = {
        "missing": list(set(expected_secret_names) - set(repo_secret_names)),
        "extra": [],
    }
    extra_secret_names = list(set(repo_secret_names) - set(expected_secret_names))
    for secret_name in extra_secret_names:
        secret_config = secrets_dict.get(secret_name, None)
        if secret_config is None:
            continue
        if not secret_config.exists:
            diff["extra"].append(secret_name)
            checked = False

    if len(diff["missing"]) > 0:
        checked = False

    return checked, diff
