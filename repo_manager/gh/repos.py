from gh import Github
from github.Repository import Repository


class BadTokenError(Exception): ...


def get_repo(client: Github, repo: str) -> tuple[bool, Repository | None]:
    """Gets a repo"""
    try:
        repo = client.get_repo(repo)
    except Exception as exc:  # this exception should be tighter
        raise BadTokenError(exc)

    return True, repo
