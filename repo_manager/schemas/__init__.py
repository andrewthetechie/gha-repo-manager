import yaml
from pydantic import BaseModel, Field  # pylint: disable=E0611
from copy import copy

from .branch_protection import BranchProtection
from .file import FileConfig
from .label import Label
from .secret import Secret
from .settings import Settings
from .collaborator import Collaborator


def empty_list():
    this_list = list()
    return copy(this_list)


class RepoManagerConfig(BaseModel):
    settings: Settings | None
    branch_protections: list[BranchProtection] = Field(default_factory=empty_list)
    secrets: list[Secret] = Field(default_factory=empty_list)
    labels: list[Label] = Field(default_factory=empty_list)
    files: list[FileConfig] = Field(default_factory=empty_list)
    collaborators: list[Collaborator] = Field(default_factory=empty_list)

    @property
    def secrets_dict(self):
        return {secret.key: secret for secret in self.secrets} if self.secrets is not None else {}

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
