from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from github.Consts import mediaTypeRequireMultipleApprovingReviews
from github.GithubException import GithubException
from github.GithubObject import NotSet
from github.Repository import Repository

from repo_manager.schemas.branch_protection import BranchProtection
from repo_manager.schemas.branch_protection import ProtectionOptions
from repo_manager.utils import attr_to_kwarg


def diff_option(key: str, expected: Any, repo_value: Any) -> Optional[str]:
    if expected is not None:
        if expected != repo_value:
            return f"{key} -- Expected: {expected} Found: {repo_value}"
    return None


def update_branch_protection(repo: Repository, branch: str, protection_config: ProtectionOptions):  # noqa: C901
    # Copied from https://github.com/PyGithub/PyGithub/blob/001970d4a828017f704f6744a5775b4207a6523c/github/Branch.py#L112
    # Until pygithub supports this, we need to do it manually
    def edit_protection(  # nosec
        branch,
        strict=NotSet,
        contexts=NotSet,
        enforce_admins=NotSet,
        dismissal_users=NotSet,
        dismissal_teams=NotSet,
        dismiss_stale_reviews=NotSet,
        require_code_owner_reviews=NotSet,
        required_approving_review_count=NotSet,
        user_push_restrictions=NotSet,
        team_push_restrictions=NotSet,
        required_linear_history=NotSet,
        allow_force_pushes=NotSet,
        allow_deletions=NotSet,
        block_creations=NotSet,
        required_conversation_resolution=NotSet,
    ):  # nosec
        """
        :calls: `PUT /repos/{owner}/{repo}/branches/{branch}/protection <https://docs.github.com/en/rest/reference/repos#get-branch-protection>`_
        :strict: bool
        :contexts: list of strings
        :enforce_admins: bool
        :dismissal_users: list of strings
        :dismissal_teams: list of strings
        :dismiss_stale_reviews: bool
        :require_code_owner_reviews: bool
        :required_approving_review_count: int
        :user_push_restrictions: list of strings
        :team_push_restrictions: list of strings
        NOTE: The GitHub API groups strict and contexts together, both must
        be submitted. Take care to pass both as arguments even if only one is
        changing. Use edit_required_status_checks() to avoid this.
        """
        assert strict is NotSet or isinstance(strict, bool), strict
        assert contexts is NotSet or all(isinstance(element, str) for element in contexts), contexts
        assert enforce_admins is NotSet or isinstance(enforce_admins, bool), enforce_admins
        assert dismissal_users is NotSet or all(
            isinstance(element, str) for element in dismissal_users
        ), dismissal_users
        assert dismissal_teams is NotSet or all(
            isinstance(element, str) for element in dismissal_teams
        ), dismissal_teams
        assert dismiss_stale_reviews is NotSet or isinstance(dismiss_stale_reviews, bool), dismiss_stale_reviews
        assert require_code_owner_reviews is NotSet or isinstance(
            require_code_owner_reviews, bool
        ), require_code_owner_reviews
        assert required_approving_review_count is NotSet or isinstance(
            required_approving_review_count, int
        ), required_approving_review_count

        post_parameters = {}
        if strict is not NotSet or contexts is not NotSet:
            if strict is NotSet:
                strict = False
            if contexts is NotSet:
                contexts = []
            post_parameters["required_status_checks"] = {
                "strict": strict,
                "contexts": contexts,
            }
        else:
            post_parameters["required_status_checks"] = None

        if enforce_admins is not NotSet:
            post_parameters["enforce_admins"] = enforce_admins
        else:
            post_parameters["enforce_admins"] = None

        if (
            dismissal_users is not NotSet
            or dismissal_teams is not NotSet
            or dismiss_stale_reviews is not NotSet
            or require_code_owner_reviews is not NotSet
            or required_approving_review_count is not NotSet
        ):
            post_parameters["required_pull_request_reviews"] = {}
            if dismiss_stale_reviews is not NotSet:
                post_parameters["required_pull_request_reviews"]["dismiss_stale_reviews"] = dismiss_stale_reviews
            if require_code_owner_reviews is not NotSet:
                post_parameters["required_pull_request_reviews"][
                    "require_code_owner_reviews"
                ] = require_code_owner_reviews
            if required_approving_review_count is not NotSet:
                post_parameters["required_pull_request_reviews"][
                    "required_approving_review_count"
                ] = required_approving_review_count
            if dismissal_users is not NotSet:
                post_parameters["required_pull_request_reviews"]["dismissal_restrictions"] = {"users": dismissal_users}
            if dismissal_teams is not NotSet:
                if "dismissal_restrictions" not in post_parameters["required_pull_request_reviews"]:
                    post_parameters["required_pull_request_reviews"]["dismissal_restrictions"] = {}
                post_parameters["required_pull_request_reviews"]["dismissal_restrictions"]["teams"] = dismissal_teams
        else:
            post_parameters["required_pull_request_reviews"] = None
        if user_push_restrictions is not NotSet or team_push_restrictions is not NotSet:
            if user_push_restrictions is NotSet:
                user_push_restrictions = []
            if team_push_restrictions is NotSet:
                team_push_restrictions = []
            post_parameters["restrictions"] = {
                "users": user_push_restrictions,
                "teams": team_push_restrictions,
            }
        else:
            post_parameters["restrictions"] = None

        if required_linear_history is not NotSet:
            post_parameters["required_linear_history"] = required_linear_history
        else:
            post_parameters["required_linear_history"] = None

        if allow_force_pushes is not NotSet:
            post_parameters["allow_force_pushes"] = allow_force_pushes
        else:
            post_parameters["allow_force_pushes"] = None

        if allow_deletions is not NotSet:
            post_parameters["allow_deletions"] = allow_deletions
        else:
            post_parameters["allow_deletions"] = None

        if block_creations is not NotSet:
            post_parameters["block_creations"] = block_creations
        else:
            post_parameters["block_creations"] = None

        if required_conversation_resolution is not NotSet:
            post_parameters["required_conversation_resolution"] = required_conversation_resolution
        else:
            post_parameters["required_conversation_resolution"] = None

        headers, data = branch._requester.requestJsonAndCheck(
            "PUT",
            branch.protection_url,
            headers={"Accept": mediaTypeRequireMultipleApprovingReviews},
            input=post_parameters,
        )

    this_branch = repo.get_branch(branch)
    kwargs = {}
    status_check_kwargs = {}
    extra_kwargs = {}

    if protection_config.pr_options is not None:
        attr_to_kwarg("required_approving_review_count", protection_config.pr_options, kwargs)
        attr_to_kwarg("dismiss_stale_reviews", protection_config.pr_options, kwargs)
        attr_to_kwarg("require_code_owner_reviews", protection_config.pr_options, kwargs)

        if repo.organization is not None:
            attr_to_kwarg(
                "users",
                protection_config.pr_options.dismissal_restrictions,
                kwargs,
                transform_key="dismissal_users",
            )
            attr_to_kwarg(
                "teams",
                protection_config.pr_options.dismissal_restrictions,
                kwargs,
                transform_key="dismissal_teams",
            )

    if repo.organization is not None:
        attr_to_kwarg(
            "users",
            protection_config.restrictions,
            kwargs,
            transform_key="user_push_restrictions",
        )
        attr_to_kwarg(
            "teams",
            protection_config.restrictions,
            kwargs,
            transform_key="team_push_restrictions",
        )

    attr_to_kwarg("enforce_admins", protection_config, kwargs)

    # these are going to be used by edit_required_status_checks
    attr_to_kwarg("strict", protection_config.required_status_checks, status_check_kwargs)
    attr_to_kwarg(
        "checks",
        protection_config.required_status_checks,
        status_check_kwargs,
        transform_key="contexts",
    )

    # these are not handled by edit_protection, so we have to use the custom api
    attr_to_kwarg(
        "require_linear_history",
        protection_config,
        extra_kwargs,
        transform_key="required_linear_history",
    )
    attr_to_kwarg("allow_force_pushes", protection_config, extra_kwargs)
    attr_to_kwarg("allow_deletions", protection_config, extra_kwargs)
    attr_to_kwarg("block_creations", protection_config, extra_kwargs)
    attr_to_kwarg(
        "require_conversation_resolution",
        protection_config,
        extra_kwargs,
        transform_key="required_conversation_resolution",
    )

    try:
        edit_protection(branch=this_branch, **kwargs, **extra_kwargs)
    except GithubException as exc:
        raise ValueError(f"{exc.data['message']} {exc.data['documentation_url']}")

    if status_check_kwargs != {}:
        try:
            this_branch.edit_required_status_checks(**status_check_kwargs)
        except GithubException as exc:
            raise ValueError(f"{exc.data['message']} {exc.data['documentation_url']}")

    # signed commits has its own method
    if protection_config.require_signed_commits is not None:
        if protection_config.require_signed_commits:
            this_branch.add_required_signatures()
        else:
            this_branch.remove_required_signatures()


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
            extra_protections.append(config_bp.name)
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

        if (
            config_bp.protection.required_status_checks is not None
            and this_protection.required_status_checks is not None
        ):
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
            diff_option(
                "enforce_admins",
                config_bp.protection.enforce_admins,
                this_protection.enforce_admins,
            )
        )
        diffs.append(
            diff_option(
                "require_linear_history",
                config_bp.protection.require_linear_history,
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
                "block_creations",
                config_bp.protection.block_creations,
                this_protection.raw_data["block_creations"]["enabled"],
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
