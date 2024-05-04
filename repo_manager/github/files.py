from pathlib import Path

from github.GithubException import UnknownObjectException
from github.Repository import Repository

from repo_manager.schemas import FileConfig


class RemoteSrcNotFoundError(Exception): ...


def copy_file(repo: Repository, file_config: FileConfig) -> str:
    """Copy files to a repository using the BLOB API
    Files can be sourced from a local file or a remote repository
    """
    target_branch = file_config.target_branch if file_config.target_branch is not None else repo.default_branch
    try:
        file_contents = (
            file_config.src_file_contents
            if not file_config.remote_src
            else get_remote_file_contents(repo, file_config.src_file, target_branch)
        )
    except UnknownObjectException:
        raise RemoteSrcNotFoundError(f"Remote file {file_config.src_file} not found in {target_branch}")

    try:
        dest_contents = repo.get_contents(str(file_config.dest_file), ref=target_branch)
        result = repo.update_file(
            str(file_config.dest_file.relative_to(".")),
            file_config.commit_msg,
            file_contents,
            sha=dest_contents.sha,
            branch=target_branch,
        )
    except UnknownObjectException:
        # if dest_contents are unknown, this is a new file
        result = repo.create_file(
            str(file_config.dest_file.relative_to(".")), file_config.commit_msg, file_contents, branch=target_branch
        )

    return result["commit"].sha


def get_remote_file_contents(repo: Repository, path: Path, target_branch: str) -> str:
    """Get the contents of a file from a remote repository"""
    contents = repo.get_contents(str(path.relative_to(".")), ref=target_branch)
    return contents.decoded_content.decode("utf-8")


def move_file(repo: Repository, file_config: FileConfig) -> tuple[str, str]:
    """Move a file from a repository"""
    return copy_file(repo, file_config), delete_file(repo, file_config)


def delete_file(
    repo: Repository,
    file_config: FileConfig,
) -> str:
    """Delete a file from a repository"""
    # if we're doing a delete for a move, delete the src_file rather than the dest_file
    to_delete = file_config.src_file if file_config.move else file_config.dest_file
    target_branch = file_config.target_branch if file_config.target_branch is not None else repo.default_branch
    contents = repo.get_contents(str(to_delete.relative_to(".")), ref=target_branch)
    result = repo.delete_file(contents.path, file_config.commit_msg, contents.sha, branch=target_branch)
    return result["commit"].sha
