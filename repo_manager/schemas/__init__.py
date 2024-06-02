import yaml
from pydantic import BaseModel, Field  # pylint: disable=E0611

from .branch_protection import BranchProtection
from .file import FileConfig
from .label import Label
from .secret import Secret
from .settings import Settings
from .environment import Environment
from .collaborator import Collaborator


class RepoManagerConfig(BaseModel):
    settings: Settings | None
    branch_protections: list[BranchProtection] | None = Field(
        None, description="Branch protections in the repo to manage"
    )
    secrets: list[Secret] | None = Field(None, description="Secrets in the repo to manage")
    variables: list[Secret] | None = Field(None, description="Variables in the repo to manage")
    labels: list[Label] | None = Field(None, description="Labels in the repo to manage")
    files: list[FileConfig] | None = Field(None, description="Files in the repo to manage")
    collaborators: list[Collaborator] | None = Field(None, description="Collaborators in the repo to manage")
    environments: list[Environment] | None = Field(None, description="Deployment Environments in the repo to manage")

    @property
    def secrets_dict(self):
        return {secret.key: secret for secret in self.secrets} if self.secrets is not None else {}

    @property
    def variables_dict(self):
        return {variable.key: variable for variable in self.variables} if self.variables is not None else {}

    @property
    def labels_dict(self):
        return {label.expected_name: label for label in self.labels} if self.labels is not None else {}

    @property
    def branch_protections_dict(self):
        return (
            {branch_protection.name: branch_protection for branch_protection in self.branch_protections}
            if self.branch_protections is not None
            else {}
        )

    @property
    def environments_dict(self):
        return (
            {environment.name: environment for environment in self.environments}
            if self.environments is not None
            else {}
        )

    @property
    def collaborators_dict(self):
        return (
            {collaborator.name: collaborator for collaborator in self.collaborators}
            if self.collaborators is not None
            else {}
        )


def load_config(filename: str) -> RepoManagerConfig:
    """Loads a yaml file into a RepoManagerconfig"""
    with open(filename) as fh:
        this_dict = yaml.safe_load(fh)

    return RepoManagerConfig.model_validate(this_dict)
