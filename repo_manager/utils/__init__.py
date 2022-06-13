import os
import sys
from typing import Any
from typing import Dict

import yaml
from actions_toolkit import core as actions_toolkit

from repo_manager.github import get_github_client


VALID_ACTIONS = {"validate": None, "check": None, "apply": None}


def get_inputs() -> Dict[str, Any]:
    """Get inputs from our workflow, valudate them, and return as a dict
    Reads inputs from actions.yaml. Non required inputs that are not set are returned as None
    Returns:
        Dict[str, Any]: [description]
    """
    parsed_inputs = dict()
    with open("action.yml") as fh:
        action_config = yaml.safe_load(fh)
    for input_name, input_config in action_config["inputs"].items():
        this_input_value = actions_toolkit.get_input(
            input_name, required=input_config.get("required", input_config.get("default", None) == None)
        )
        parsed_inputs[input_name] = this_input_value if this_input_value != "" else None
        # set defaults from actions.yaml if not running in github, this is for local testing
        # https://docs.github.com/en/actions/learn-github-actions/environment-variables
        if (
            os.environ.get("CI", "false").lower() == "false"
            and os.environ.get("GITHUB_ACTIONS", "false").lower() == "false"
        ):
            if parsed_inputs[input_name] is None:
                parsed_inputs[input_name] = input_config.get("default", None)
                if parsed_inputs[input_name] is None:
                    actions_toolkit.set_failed(f"Error getting inputs. {input_name} is missing a default")

    # validate our inputs
    parsed_inputs["action"] = parsed_inputs["action"].lower()
    if parsed_inputs["action"] not in VALID_ACTIONS.keys():
        actions_toolkit.set_failed(
            f"Error while loading RepoManager Config. {parsed_inputs['action']} is not a valid action in {VALID_ACTIONS.keys()}"
        )

    if not os.path.exists(parsed_inputs["settings_file"]):
        actions_toolkit.set_failed(
            f"Error while loading RepoManager Config. {parsed_inputs['settings_file']} does not exist"
        )

    if parsed_inputs["repo"] != "self":
        if len(parsed_inputs["repo"].split("/")) != 2:
            actions_toolkit.set_failed(
                f"Error while loading RepoManager Config. {parsed_inputs['repo']} is not a valid github repo. Please be sure to enter in the style of 'owner/repo-name'."
            )
    else:
        parsed_inputs["repo"] = os.environ.get("GITHUB_REPOSITORY", None)
        if parsed_inputs["repo"] is None:
            actions_toolkit.set_failed(
                f"Error getting inputs. repo is 'self' and GITHUB_REPOSITORY env var is not set. Please set INPUT_REPO or GITHUB_REPOSITORY in the env"
            )

    try:
        repo = get_github_client(parsed_inputs["token"]).get_repo(parsed_inputs["repo"])
    except Exception as exc:  # this should be tighter
        actions_toolkit.set_failed(f"Error while retriving {parsed_inputs['repo']} from Github. {exc}")

    parsed_inputs["repo_object"] = repo

    return parsed_inputs
