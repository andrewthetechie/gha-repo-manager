from pydantic import BaseModel  # pylint: disable=E0611
from typing import Annotated
from pydantic import Field

OptBool = bool | None
OptStr = str | None


class RestrictionOptions(BaseModel):
    users: list[str] | None = Field(
        None, description="List of users who cannot push to this branch, only available to orgs"
    )
    teams: list[str] | None = Field(
        None, description="List of teams who cannot push to this branch, only available to orgs"
    )


class StatusChecksOptions(BaseModel):
    strict: OptBool = Field(False, description="Require branches to be up to date before merging.")
    checks: list[str] | None = Field(
        [], description="The list of status checks to require in order to merge into this branch"
    )


class DismissalOptions(BaseModel):
    users: list[str] | None = Field(
        None, description="List of users who can dismiss pull request reviews, only available to orgs"
    )
    teams: list[str] | None = Field(
        None, description="List of teams who can dismiss pull request reviews, only available to orgs"
    )


class PROptions(BaseModel):
    required_approving_review_count: Annotated[int, Field(strict=True, gt=1, le=6)] | None = Field(
        None, description="The number of approvals required. (1-6)"
    )
    dismiss_stale_reviews: OptBool = Field(
        None, description="Dismiss approved reviews automatically when a new commit is pushed."
    )
    require_code_owner_reviews: OptBool = Field(None, description="Blocks merge until code owners have reviewed.")
    dismissal_restrictions: DismissalOptions | None = Field(
        None, description="Options related to PR dismissal. Only available to Orgs. Not available in the Check command"
    )


class ProtectionOptions(BaseModel):
    pr_options: PROptions | None = Field(None, description="Options related to PR reviews")
    required_status_checks: StatusChecksOptions | None = Field(
        StatusChecksOptions(), description="Options related to required status checks"
    )
    enforce_admins: OptBool = Field(
        None,
        description="Enforce all configured restrictions for administrators. Set to true to enforce required status "
        + "checks for repository administrators. Set to null to disable.",
    )
    require_linear_history: OptBool = Field(
        None, description="Prevent merge commits from being pushed to matching branches"
    )
    restrictions: RestrictionOptions | None = Field(
        None, description="Options related to restricting who can push to this branch"
    )
    allow_force_pushes: OptBool = Field(None, description="Permit force pushes for all users with push access.")
    allow_deletions: OptBool = Field(None, description="Allow users with push access to delete matching branches.")
    block_creations: OptBool = Field(
        None,
        description="If set to true, the restrictions branch protection settings which limits who can push "
        + "will also block pushes which create new branches, unless the push is initiated by a user, team, or "
        + "app which has the ability to push. Set to true to restrict new branch creation.",
    )

    require_conversation_resolution: OptBool = Field(
        None,
        description="When enabled, all conversations on code must be resolved before a pull request can be merged.",
    )
    require_signed_commits: OptBool = Field(
        None, description="Commits pushed to matching branches must have verified signatures."
    )


class BranchProtection(BaseModel):
    name: OptStr = Field(None, description="Name of the branch")
    protection: ProtectionOptions | None = Field(None, description="Protection options for the branch")
    exists: OptBool = Field(True, description="Set to false to delete a branch protection rule")
