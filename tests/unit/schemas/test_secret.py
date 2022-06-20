import os
import random
import string
from copy import deepcopy

import pytest
import yaml
from pydantic import ValidationError

from repo_manager.schemas import Secret
from repo_manager.schemas.secret import SecretEnvError


VALID_CONFIG = {
    "key": "test",
    "env": "test",
}


def test_valid_secret():
    this_secret = Secret(**VALID_CONFIG)
    assert this_secret.key == "test"
    assert this_secret.env == "test"
    assert this_secret.value is None
    assert this_secret.required


def test_secret_validate_value():
    value_config = deepcopy(VALID_CONFIG)
    value_config["value"] = "test"
    with pytest.raises(ValidationError):
        Secret(**value_config)

    value_config["env"] = None
    this_secret = Secret(**value_config)
    assert this_secret.value == "test"


def test_secret_expected_value():
    this_config = deepcopy(VALID_CONFIG)
    this_config["env"] = "".join(random.choices(string.ascii_lowercase, k=16))
    this_secret = Secret(**this_config)

    with pytest.raises(SecretEnvError):
        this_secret.expected_value

    os.environ[this_config["env"]] = "test"
    assert this_secret.expected_value == "test"

    value_config = deepcopy(VALID_CONFIG)
    value_config["env"] = None
    value_config["value"] = "bar"
    value_secret = Secret(**value_config)

    assert value_secret.expected_value == "bar"


def test_example_works():
    with open("examples/settings.yml") as fh:
        example_data = yaml.safe_load(fh)

    assert len(example_data["secrets"]) > 0
    for secret in example_data["secrets"]:
        Secret(**secret)
