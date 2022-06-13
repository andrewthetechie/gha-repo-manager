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


def load_config(filename: str) -> RepoManagerConfig:
    """Loads a yaml file into a RepoManagerconfig"""
    with open(filename) as fh:
        this_dict = yaml.safe_load(fh)

    return RepoManagerConfig(**this_dict)
