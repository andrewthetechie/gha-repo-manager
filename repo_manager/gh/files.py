import os
import shutil
from pathlib import Path
from typing import Any

from git import Repo, Commit

from actions_toolkit import core as actions_toolkit
from github.GithubException import GithubException
from github.Repository import Repository

from repo_manager.schemas import FileConfig
from repo_manager.utils import get_inputs


commitChanges: Commit = None
commitCleanup: Commit = None


def __clone_repo__(repo: Repository, branch: str) -> Repo:
    """Clone a repository to the local filesystem"""
    inputs = get_inputs()
    repo_dir = Path(inputs["workspace_path"]) / repo.name
    if repo_dir.is_dir():
        raise FileExistsError(f"Directory {repo_dir} already exists")
    cloned_repo = Repo.clone_from(repo.clone_url, str(repo_dir))
    cloned_repo.git.checkout(branch)
    return cloned_repo


def check_files(repo: Repository, files: list[FileConfig]) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Check files in a repository"""

    # if no files are provided, return True
    if files is None:
        return True, None

    inputs = get_inputs()
    target_branch = files[0].target_branch if files[0].target_branch is not None else repo.default_branch

    if inputs["repo"] == "self":
        repo_dir = Repo(".")
    else:
        # clone the repo
        repo_dir = __clone_repo__(repo, target_branch)

    diffs = {}
    extra = set[str]()
    missing = set[str]()
    moved = set[str]()
    changed = set[str]()

    # First we handle file movement and removal
    for file_config in files:
        if target_branch != (files[0].target_branch if files[0].target_branch is not None else repo.default_branch):
            raise ValueError("All files must have the same target_branch")
        oldPath = Path(repo_dir.working_tree_dir) / file_config.src_file
        newPath = Path(repo_dir.working_tree_dir) / file_config.dest_file
        # prior method used source if move was true, dest if not
        if not file_config.exists:
            fileToDelete = oldPath if file_config.move else newPath
            if fileToDelete.exists():
                os.remove(fileToDelete)
                extra.add(str(fileToDelete))
                actions_toolkit.info(f"Deleted {str(fileToDelete.relative_to(repo_dir.working_tree_dir))}")
            else:
                actions_toolkit.warning(
                    f"{str(fileToDelete)} does not exist in {target_branch} branch."
                    + "Because this is a delete, not failing run"
                )
        else:
            if file_config.exists and file_config.remote_src and not oldPath.exists():
                raise FileNotFoundError(f"File {file_config.src_file} does not exist in {repo}")
            if not (oldPath.exists() or newPath.exists()):
                missing.add(str(file_config.dest_file))
            if oldPath == newPath:
                continue  # Nothing to do
            if file_config.move:
                if not oldPath.exists():
                    actions_toolkit.warning(
                        f"{str(file_config.src_file)} does not exist in {target_branch} branch."
                        + "Because this is not a remote file, not failing run as it may be created later"
                    )
                else:
                    os.rename(oldPath, newPath)
                    moved += str(file_config.src_file)
                    actions_toolkit.info(f"Moved {str(file_config.src_file)} to {str(file_config.dest_file)}")
            elif file_config.remote_src:
                shutil.copyfile(oldPath, newPath)
                actions_toolkit.info("Copied {str(file_config.src_file)} to {str(file_config.dest_file)}")

    # we commit these changes so that deleted files and renamed files are accounted for
    global commitCleanup
    repo_dir.git.add("-A")
    if repo_dir.index.diff("HEAD") == []:
        commitCleanup = None
        actions_toolkit.debug("No files to delete or move")
    else:
        commitCleanup = repo_dir.index.commit("chore(repo_manager): Internal File Maintenance")

    if len(extra) > 0:
        diffs["extra"] = list(extra)

    if len(missing) > 0:
        diffs["missing"] = list(missing)

    # now we handle file content changes
    for file_config in files:
        if not file_config.exists or file_config.remote_src:
            continue  # we already handled this file
        srcPath = file_config.src_file
        destPath = Path(repo_dir.working_tree_dir) / file_config.dest_file
        if file_config.exists:
            if newPath.exists():
                os.remove(newPath)  # Delete the file
            shutil.copyfile(srcPath, destPath)
            actions_toolkit.info(f"Copied {str(file_config.src_file)} to {str(file_config.dest_file)}")

    # we commit the file updates (e.g. content changes)
    global commitChanges
    repo_dir.git.add("-A")
    if repo_dir.index.diff("HEAD") == []:
        commitChanges = None
        actions_toolkit.debug("No files changed")
    else:
        commitChanges = repo_dir.index.commit("chore(repo_manager): File updates")

    # get the list of files that changed content
    if commitChanges is not None:
        for file in commitChanges.stats.files:
            if str(Path(file)) not in missing:
                changed.add(str(Path(file)))

    changed.update(moved)

    if len(changed) > 0:
        diffs["diff"] = list(changed)

    if len(diffs) > 0:
        return False, diffs
    # actions_toolkit.info("Commit SHAs: " + ",".join(commits))
    # Default to no differences
    return True, None


def update_files(
    repo: Repository, files: list[FileConfig], diffs: tuple[dict[str, list[str] | dict[str, Any]]]
) -> set[str]:
    """Update files in a repository"""
    errors = set[str]()
    if diffs is None:
        return errors
    inputs = get_inputs()
    target_branch = files[0].target_branch if files[0].target_branch is not None else repo.default_branch

    if inputs["repo"] == "self":
        repo_dir = Repo.init(".")
    else:
        repoPath = Path(inputs["workspace_path"]) / repo.name
        if not repoPath.exists:
            raise FileExistsError(f"Directory {repoPath} does not exist!")
        if not repoPath.is_dir():
            raise NotADirectoryError(f"{repoPath} is not a directory!")
        repo_dir = Repo(repoPath)

    if repo_dir.active_branch.name != target_branch:
        raise ValueError("Target branch does not match active branch")

    origin = repo_dir.remote()
    pushInfo = origin.push()

    if pushInfo.error is not None:
        for info in pushInfo:
            if info.ERROR:
                errors.append(
                    {
                        "type": "file-update",
                        "key": info.local_ref.commit.hexsha,
                        "error": f"{GithubException(info.ERROR, message = info.summary)}",
                    }
                )

    return errors
