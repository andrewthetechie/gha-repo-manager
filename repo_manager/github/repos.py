from typing import Optional
from typing import Tuple

from github import Github
from github.Repository import Repository


class BadTokenError(Exception):
    ...


def get_repo(client: Github, repo: str) -> Tuple[bool, Optional[Repository]]:
    """Gets a repo"""
    try:
        repo = client.get_repo(repo)
    except Exception as exc:  # this exception should be tighter
        raise BadTokenError()

    return True, repo
