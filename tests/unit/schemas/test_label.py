import random
import string
from copy import deepcopy

import yaml

from repo_manager.schemas import Label


VALID_CONFIG = {
    "name": "test",
    "color": "ff00ff",
    "description": "test",
}


def test_valid_config():
    this_label = Label(**VALID_CONFIG)
    assert this_label.name == "test"
    assert this_label.color.as_hex() == "#f0f"
    assert this_label.description == "test"
    assert this_label.exists


def test_color_no_hash():
    this_label = Label(**VALID_CONFIG)
    assert this_label.color_no_hash == "f0f"

    no_color_config = deepcopy(VALID_CONFIG)
    no_color_config["color"] = None
    no_color_label = Label(**no_color_config)
    assert no_color_label.color_no_hash is None


def test_expected_name():
    this_config = deepcopy(VALID_CONFIG)
    this_config["new_name"] = "".join(random.choices(string.ascii_lowercase, k=16))
    this_label = Label(**this_config)

    assert this_label.expected_name == this_config["new_name"]


def test_example_works():
    with open("examples/settings.yml") as fh:
        example_data = yaml.safe_load(fh)

    assert len(example_data["labels"]) > 0
    for label in example_data["labels"]:
        Label(**label)
