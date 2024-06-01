from typing import Optional, Self

from github import Github
from github.EnvironmentDeploymentBranchPolicy import EnvironmentDeploymentBranchPolicyParams
from github.EnvironmentProtectionRuleReviewer import ReviewerParams

from repo_manager.utils import get_client, get_repo

from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field, field_validator, model_validator

from .secret import Secret

OptBool = Optional[bool]
OptStr = Optional[str]
OptInt = Optional[int]


class Reviewer(BaseModel):
    type: str = Field("team", description="Type of reviewer, can be `user` or `team`")
    name: str = Field(
        "andrewthetechie",
        description="Name of the reviewer, either a user or team name",
    )
    id: int = Field(0, description="ID of the reviewer, either a user or team ID")

    @model_validator(mode="after")
    def initialize_id(self) -> Self:
        client: Github = get_client()
        if self.type == "User":
            self.id = int(client.get_user(self.name).id)
        elif self.type == "Team":
            if self.name.count("/") == 1:
                org, team = self.name.split("/")
            else:
                org = get_repo().owner.login
                team = self.name
            self.id = int(client.get_organization(org).get_team_by_slug(team).id)
        return self

    @field_validator("type")
    def validate_type(cls, v) -> str:
        v = v.lower().capitalize()
        if v not in {"User", "Team"}:
            raise ValueError("Reviewer Type must be user or team.")
        return v

    def get_ReviewerParams(self) -> ReviewerParams:
        return ReviewerParams(self.type, self.id)


class DeploymentBranchPolicy(BaseModel):
    protected_branches: bool = Field(
        None,
        description="Restrict deployment to environment from protected branches only",
    )
    custom_branch_policies: bool = Field(
        None,
        description="Restrict deployment to environment from custom branch policies only",
    )

    @model_validator(mode="after")
    def initialize_branch_name_patterns(self) -> Self:
        if self.protected_branches == self.custom_branch_policies:
            raise ValueError("You must specify either protected branches or custom branch policies, not both.")
        return self

    def get_EnvironmentDeploymentBranchPolicyParams(self) -> EnvironmentDeploymentBranchPolicyParams:
        return EnvironmentDeploymentBranchPolicyParams(self.protected_branches, self.custom_branch_policies)


class Environment(BaseModel):
    name: str = Field(..., description="Name of the environment")
    secrets: list[Secret] | None = Field(None, description="Environment Secrets.")
    variables: list[Secret] | None = Field(None, description="Environment Variables.")
    exists: OptBool = Field(True, description="Set to false to delete an environment")
    wait_timer: OptInt = Field(
        None,
        strict=True,
        ge=0,
        le=43200,
        description="The amount of time to delay a job after the job is initially triggered. "
        + "The time (in minutes) must be an integer between 0 and 43,200 (30 days)",
    )
    prevent_self_review: bool = Field(
        True,
        description="Whether or not a user who created the job is prevented from approving their own job.",
    )
    reviewers: list[Reviewer] = Field(
        [],
        description="The people or teams that may review jobs that reference the environment. "
        + "You can list up to six users or teams as reviewers. "
        + "The reviewers must have at least read access to the repository. "
        + "Only one of the required reviewers needs to approve the job for it to proceed.",
    )
    deployment_branch_policy: DeploymentBranchPolicy | None = Field(
        None,
        description="The type of deployment branch policy for this environment. "
        + "To allow all branches to deploy, set to null.",
    )
    branch_name_patterns: set[str] = Field(
        [],
        description="List of branch name patterns deployments to this environment are restricted to; "
        + "if list is empty the restriction is either None or protected branches.",
    )

    @model_validator(mode="after")
    def initialize_branch_name_patterns(self) -> Self:
        if self.deployment_branch_policy is None:
            return self
        if len(self.branch_name_patterns) == 0 and self.deployment_branch_policy.custom_branch_policies:
            raise ValueError("You must specify branch name patterns if custom branch policies are enabled.")
        if len(self.branch_name_patterns) > 0 and not self.deployment_branch_policy.custom_branch_policies:
            raise ValueError("You must enable custom branch policies to specify branch name patterns.")
        return self

    @field_validator("reviewers")
    def validate_reviewers(cls, v) -> list[Reviewer]:
        if len(v) > 6:
            raise ValueError("You can only have up to 6 reviewers.")
        return v

    def get_ReviewerParams(self) -> list[ReviewerParams]:
        return [reviewer.get_ReviewerParams() for reviewer in self.reviewers]

    def get_EnvironmentDeploymentBranchPolicyParams(self) -> EnvironmentDeploymentBranchPolicyParams:
        return self.deployment_branch_policy.get_EnvironmentDeploymentBranchPolicyParams()
