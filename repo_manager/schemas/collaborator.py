from typing import Self

from github import Github

from repo_manager.utils import get_client, get_repo

from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field, field_validator, model_validator


class Collaborator(BaseModel):
    type: str = Field("team", description="Type of reviewer, can be `user` or `team`")
    name: str = Field("user", description="Name of the reviewer, either a user or team name")
    permission: str = Field(
        "pull",
        description="Permission level of the reviewer, can be `pull` `triage`, "
        + "`push`, `maintain`, `admin`, or custom roles defined in the repo/org",
    )
    exists: bool = Field(
        True,
        description="Whether the collaborator should exist in the repo; "
        + "mark as false to remove the collaborator from the repo",
    )
    id: int = Field(0, description="ID of the reviewer, either a user or team ID")
    repositories_url: str = Field(None, description="URL to modify team permissions, only applicable for teams")

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
            github_object = client.get_organization(org).get_team_by_slug(team)
            self.repositories_url = github_object.repositories_url
            self.id = github_object.id
        return self

    @field_validator("type")
    def validate_type(cls, v) -> str:
        v = v.lower().capitalize()
        if v not in {"User", "Team"}:
            raise ValueError("Reviewer Type must be user or team.")
        return v
