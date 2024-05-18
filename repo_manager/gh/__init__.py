from functools import lru_cache

from github import Github
from github.GithubException import GithubException
from github.GithubException import UnknownObjectException


@lru_cache
def get_github_client(token: str, api_url: str) -> Github:
    """ """
    return Github(token, base_url=api_url)


__all__ = ["get_github_client", "GithubException", "UnknownObjectException"]
