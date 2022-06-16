from typing import List
from typing import Optional
from typing import Union

import yaml
from pydantic import BaseModel  # pylint: disable=E0611
from pydantic import Field

from .branch_protection import BranchProtection
from .label import Label
from .secret import Secret
from .settings import Settings


class RepoManagerConfig(BaseModel):
    settings: Optional[Settings]
    branch_protections: Optional[List[BranchProtection]]
    secrets: Optional[List[Secret]]
    labels: Optional[List[Label]]

    @property
    def secrets_dict(self):
        return {secret.key for secret in self.secrets} if self.secrets is not None else {}

    @property
    def labels_dict(self):
        return {label.expected_name for label in self.labels} if self.labels is not None else {}

    @property
    def branch_protections_dict(self):
        return (
            {branch_protection.name for branch_protection in self.branch_protections}
            if self.branch_protections is not None
            else {}
        )


def load_config(filename: str) -> RepoManagerConfig:
    """Loads a yaml file into a RepoManagerconfig"""
    with open(filename) as fh:
        this_dict = yaml.safe_load(fh)

    return RepoManagerConfig(**this_dict)
