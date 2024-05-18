from copy import deepcopy
from typing import Any

from github.Repository import Repository

from repo_manager.schemas.label import Label


def update_label(repo: Repository, label: Label):
    this_label = repo.get_label(label.name)
    color = this_label.color if label.color_no_hash is None else label.color_no_hash
    description = this_label.description if label.description is None else label.description
    this_label.edit(label.expected_name, color, description)


def check_repo_labels(
    repo: Repository, config_labels: list[Label]
) -> tuple[bool, dict[str, list[str] | dict[str, Any]]]:
    """Checks a repo's labels vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    """
    repo_labels = {label.name: label for label in repo.get_labels()}

    missing_labels = []
    extra_labels = []
    diff_labels = {}

    for config_label in config_labels:
        repo_label = repo_labels.get(config_label.expected_name, None)
        if repo_label is None and config_label.exists:
            missing_labels.append(config_label.expected_name)
            continue
        if not config_label.exists and repo_label is not None:
            extra_labels.append(config_label.expected_name)
            continue

        diffs = []
        if config_label.color is not None:
            if config_label.color_no_hash != repo_label.color:
                diffs.append(f"Expected color '{config_label.color_no_hash}'. Repo has color '{repo_label.color}'")

        if config_label.description is not None:
            if config_label.description != repo_label.description:
                diffs.append(
                    f"Expected description '{config_label.description}'. Repo description '{repo_label.description}"
                )
        if len(diffs) > 0:
            diff_labels[config_label.expected_name] = deepcopy(diffs)

    return len(missing_labels) == 0 & len(extra_labels) == 0 & len(diff_labels.keys()) == 0, {
        "missing": missing_labels,
        "extra": extra_labels,
        "diffs": diff_labels,
    }
