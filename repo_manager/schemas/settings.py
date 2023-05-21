from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field
from pydantic import HttpUrl  # pylint: disable=E0611


OptBool = bool | None
OptStr = str | None


class Settings(BaseModel):
    description: OptStr = Field(None, description="A short description of the repository that will show up on GitHub.")
    homepage: str | HttpUrl | None = Field(None, description="A URL with more information about the repository.")
    topics: str | list[str] | None = Field(None, description="A list of strings to apply as topics on the repo")
    private: OptBool = Field(
        None, description="Either `true` to make the repository private, or `false` to make it public."
    )
    has_issues: OptBool = Field(
        None, description="Either `true` to enable issues for this repository, `false` to disable them."
    )
    has_projects: OptBool = Field(
        None,
        description="Either `true` to enable projects for this repository, or `false` to disable them. "
        + "If projects are disabled for the organization, passing `true` will cause an API error.",
    )
    has_wiki: OptBool = Field(
        None, description="Either `true` to enable the wiki for this repository, `false` to disable it."
    )
    has_downloads: OptBool = Field(
        None, description="Either `true` to enable downloads for this repository, `false` to disable them."
    )
    default_branch: OptStr = Field(None, description="Set the default branch for this repository. ")
    allow_squash_merge: OptBool = Field(
        None, description="Either `true` to allow squash-merging pull requests, or `false` to prevent squash-merging."
    )
    allow_merge_commit: OptBool = Field(
        None,
        description="Either `true` to allow merging pull requests with a merge commit, or `false` to prevent "
        + "merging pull requests with merge commits.",
    )
    allow_rebase_merge: OptBool = Field(
        None,
        description="  # Either `true` to allow rebase-merging pull requests, or `false` to prevent rebase-merging.",
    )
    delete_branch_on_merge: OptBool = Field(
        None, description="Either `true` to enable automatic deletion of branches on merge, or `false` to disable"
    )
    enable_automated_security_fixes: OptBool = Field(
        None,
        description="Either `true` to enable automated security fixes, or `false` to disable automated security fixes.",
    )
    enable_vulnerability_alerts: OptBool = Field(
        None, description="Either `true` to enable vulnerability alerts, or `false` to disable vulnerability alerts."
    )
