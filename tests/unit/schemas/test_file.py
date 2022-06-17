import random
import string
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from repo_manager.schemas import FileConfig


VALID_CONFIG = {
    "src_file": "tests/unit/schemas/test_file.py",
    "dest_file": "test",
}


def test_file_valid_config():
    this_file_config = FileConfig(**VALID_CONFIG)
    assert this_file_config.src_file == Path(VALID_CONFIG["src_file"])
    assert this_file_config.dest_file == Path(VALID_CONFIG["dest_file"])
    assert this_file_config.move is False
    assert this_file_config.exists
    assert this_file_config.commit_msg == "repo_manager file commit"
    assert this_file_config.target_branch is None
    assert this_file_config.src_file_exists
    assert this_file_config.remote_src is False


def test_file_src_file_exists():
    this_file_config = FileConfig(**VALID_CONFIG)
    assert this_file_config.src_file_exists

    missing_file = deepcopy(VALID_CONFIG)
    missing_file["src_file"] = "".join(random.choices(string.ascii_lowercase, k=16))
    missing_file_config = FileConfig(**missing_file)
    assert missing_file_config.src_file_exists is False
    with pytest.raises(ValueError):
        missing_file_config.src_file_contents

    executable_file = deepcopy(VALID_CONFIG)
    executable_file["src_file"] = "./.github/scripts/replace_inputs.sh"
    executable_file["mode"] = "100755"
    executable_config = FileConfig(**executable_file)
    assert executable_config.src_file_exists


def test_file_args_validation():
    invalid_config = deepcopy(VALID_CONFIG)
    invalid_config["src_file"] = None
    with pytest.raises(ValidationError):
        FileConfig(**invalid_config)
    invalid_config = deepcopy(VALID_CONFIG)
    invalid_config["dest_file"] = None
    with pytest.raises(ValidationError):
        FileConfig(**invalid_config)


def test_example_works():
    with open("examples/settings.yml") as fh:
        example_data = yaml.safe_load(fh)

    assert len(example_data["files"]) > 0
    for file_config_dict in example_data["files"]:
        FileConfig(**file_config_dict)


def test_file_commit_key():
    this_file_config = FileConfig(**VALID_CONFIG)
    assert this_file_config.commit_key == "repo_manager file commit_"

    this_file_config.target_branch = "master"
    assert this_file_config.commit_key == "repo_manager file commit_master"

    this_file_config.target_branch = "develop"
    assert this_file_config.commit_key == "repo_manager file commit_develop"
