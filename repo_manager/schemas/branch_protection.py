from typing import List
from typing import Optional

from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import conint
from pydantic import Field

OptBool = Optional[bool]
OptStr = Optional[str]


class RestrictionOptions(BaseModel):
    users: Optional[List[str]] = Field(
        None, description="List of users who cannot push to this branch, only available to orgs"
    )
    teams: Optional[List[str]] = Field(
        None, description="List of teams who cannot push to this branch, only available to orgs"
    )


class StatusChecksOptions(BaseModel):
    strict: OptBool = Field(None, description="Require branches to be up to date before merging.")
    checks: Optional[List[str]] = Field(
        None, description="The list of status checks to require in order to merge into this branch"
    )


class DismissalOptions(BaseModel):
    users: Optional[List[str]] = Field(
        None, description="List of users who can dismiss pull request reviews, only available to orgs"
    )
    teams: Optional[List[str]] = Field(
        None, description="List of teams who can dismiss pull request reviews, only available to orgs"
    )


class PROptions(BaseModel):
    required_approving_review_count: Optional[conint(ge=1, le=6)] = Field(
        None, description="The number of approvals required. (1-6)"
    )
    dismiss_stale_reviews: OptBool = Field(
        None, description="Dismiss approved reviews automatically when a new commit is pushed."
    )
    require_code_owner_reviews: OptBool = Field(None, description="Blocks merge until code owners have reviewed.")
    dismissal_restrictions: Optional[DismissalOptions] = Field(
        None, description="Options related to PR dismissal. Only available to Orgs. Not available in the Check command"
    )


class ProtectionOptions(BaseModel):
    pr_options: Optional[PROptions] = Field(None, description="Options related to PR reviews")
    required_status_checks: Optional[StatusChecksOptions] = Field(
        None, description="Options related to required status checks"
    )
    enforce_admins: OptBool = Field(
        None,
        description="Enforce all configured restrictions for administrators. Set to true to enforce required status checks for repository administrators. Set to null to disable.",
    )
    require_linear_history: OptBool = Field(
        None, description="Prevent merge commits from being pushed to matching branches"
    )
    restrictions: Optional[RestrictionOptions] = Field(
        None, description="Options related to restricting who can push to this branch"
    )
    allow_force_pushes: OptBool = Field(None, description="Permit force pushes for all users with push access.")
    allow_deletions: OptBool = Field(None, description="Allow users with push access to delete matching branches.")
    block_creations: OptBool = Field(
        None,
        description="If set to true, the restrictions branch protection settings which limits who can push will also block pushes which create new branches, unless the push is initiated by a user, team, or app which has the ability to push. Set to true to restrict new branch creation.",
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
    protection: Optional[ProtectionOptions] = Field(None, description="Protection options for the branch")
    exists: OptBool = Field(True, description="Set to false to delete a branch protection rule")
