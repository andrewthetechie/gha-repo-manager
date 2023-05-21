from functools import lru_cache

from github import Github


@lru_cache
def get_github_client(url: str, token: str) -> Github:
    """ """
    return Github(base_url = url, login_or_token = token)
