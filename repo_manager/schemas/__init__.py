import yaml
from pydantic import BaseModel  # pylint: disable=E0611

from .branch_protection import BranchProtection
from .file import FileConfig
from .label import Label
from .secret import Secret
from .settings import Settings
from .environment import environment
from .collaborator import Collaborator


class RepoManagerConfig(BaseModel):
    settings: Settings | None
    branch_protections: list[BranchProtection] | None
    secrets: list[Secret] | None
    variables: list[Secret] | None
    labels: list[Label] | None
    files: list[FileConfig] | None
    environments: list[environment] | None
    collaborators: list[Collaborator] | None

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

    return RepoManagerConfig(**this_dict)
