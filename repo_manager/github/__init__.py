from functools import lru_cache

from github import Github


@lru_cache
def get_github_client(token: str, api_url: str) -> Github:
    """ """
    return Github(token, base_url=api_url)
