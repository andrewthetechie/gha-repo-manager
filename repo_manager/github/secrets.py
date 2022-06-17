import json
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from github.Repository import Repository

from repo_manager.schemas.secret import Secret


def upsert_secret(repo: Repository, secret_key: str, secret_config: Secret):
    ...


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
