import json
from collections.abc import Callable
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from github.Repository import Repository

from repo_manager.schemas.branch_protection import BranchProtection


def diff_option(key: str, expected: Any, repo_value: Any) -> Optional[str]:
    if expected is not None:
        if expected != repo_value:
            return f"{key} -- Expected: {expected} Found: {repo_value}"
    return None


def update_branch_protection():
    ...


def check_repo_branch_protections(
    repo: Repository, config_branch_protections: List[BranchProtection]
) -> Tuple[bool, Dict[str, Union[List[str], Dict[str, Any]]]]:
    """Checks a repo's branch protections vs our expected settings

    Args:
        repo (Repository): [description]
        secrets (List[Secret]): [description]

    """
    repo_branches = {branch.name: branch for branch in repo.get_branches()}

    missing_protections = []
    extra_protections = []
    diff_protections = {}

    for config_bp in config_branch_protections:
        repo_bp = repo_branches.get(config_bp.name, None)
        if repo_bp is None and config_bp.exists:
            missing_protections.append(config_bp.name)
            continue
        if not config_bp.exists and repo_bp is not None:
            extra_labels.append(config_bp.name)
            continue

        diffs = []
        if config_bp.protection is None:
            continue

        # if our repo isn't protected and we've made it this far, it should be
        if not repo_bp.protected:
            diff_protections[config_bp.name] = ["Branch is not protected"]
            continue

        this_protection = repo_bp.get_protection()
        if config_bp.protection.pr_options is not None:
            diffs.append(
                diff_option(
                    "required_approving_review_count",
                    config_bp.protection.pr_options.required_approving_review_count,
                    this_protection.required_pull_request_reviews.required_approving_review_count,
                )
            )
            diffs.append(
                diff_option(
                    "dismiss_stale_reviews",
                    config_bp.protection.pr_options.dismiss_stale_reviews,
                    this_protection.required_pull_request_reviews.dismiss_stale_reviews,
                )
            )
            diffs.append(
                diff_option(
                    "require_code_owner_reviews",
                    config_bp.protection.pr_options.require_code_owner_reviews,
                    this_protection.required_pull_request_reviews.require_code_owner_reviews,
                )
            )
            # for now, not checking dismissal options. Will note that in the docs

        if config_bp.protection.required_status_checks is not None:
            diffs.append(
                diff_option(
                    "required_status_checks::strict",
                    config_bp.protection.required_status_checks.strict,
                    this_protection.required_status_checks.strict,
                )
            )
            diffs.append(
                diff_option(
                    "required_status_checks::checks",
                    config_bp.protection.required_status_checks.checks,
                    this_protection.required_status_checks.contexts,
                )
            )

        diffs.append(
            diff_option("enforce_admins", config_bp.protection.enforce_admins, this_protection.enforce_admins)
        )
        diffs.append(
            diff_option(
                "required_linear_history",
                config_bp.protection.required_linear_history,
                this_protection.raw_data["required_linear_history"]["enabled"],
            )
        )
        diffs.append(
            diff_option(
                "allow_force_pushes",
                config_bp.protection.allow_force_pushes,
                this_protection.raw_data["allow_force_pushes"]["enabled"],
            )
        )
        diffs.append(
            diff_option(
                "allow_deletions",
                config_bp.protection.allow_deletions,
                this_protection.raw_data["allow_deletions"]["enabled"],
            )
        )
        diffs.append(
            diff_option(
                "require_conversation_resolution",
                config_bp.protection.require_conversation_resolution,
                this_protection.raw_data["required_conversation_resolution"]["enabled"],
            )
        )
        diffs.append(
            diff_option(
                "require_signed_commits",
                config_bp.protection.require_signed_commits,
                this_protection.raw_data["required_signatures"]["enabled"],
            )
        )

        # TODO: Figure out how to diff Restriction options

        diffs = [i for i in diffs if i is not None]
        if len(diffs) > 0:
            diff_protections[config_bp.name] = deepcopy(diffs)

    return len(missing_protections) == 0 & len(extra_protections) == 0 & len(diff_protections.keys()) == 0, {
        "missing": missing_protections,
        "extra": extra_protections,
        "diffs": diff_protections,
    }
