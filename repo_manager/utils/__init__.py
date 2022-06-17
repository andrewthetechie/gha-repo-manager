import os
from typing import Any
from typing import Dict

from actions_toolkit import core as actions_toolkit

from repo_manager.github import get_github_client

# This code is automatically generated by actions.yml and make generate-inputs
###START_INPUT_AUTOMATION###
INPUTS = {
    "action": {
        "description": "What action to take with this action. One of validate, check, or apply. Validate will validate your settings file, but not touch your repo. Check will check your repo with your settings file and output a report of any drift. Apply will apply the settings in your settings file to your repo",
        "default": "check",
    },
    "settings_file": {
        "description": "What yaml file to use as your settings. This is local to runner running this action.",
        "default": ".github/settings.yml",
    },
    "repo": {
        "description": "What repo to perform this action on. Default is self, as in the repo this action is running in",
        "default": "self",
    },
    "token": {"description": "What github token to use with this action.", "required": True},
}
###END_INPUT_AUTOMATION###

VALID_ACTIONS = {"validate": None, "check": None, "apply": None}


def get_inputs() -> Dict[str, Any]:
    """Get inputs from our workflow, valudate them, and return as a dict
    Reads inputs from the dict INPUTS. This dict is generated from the actions.yml file.
    Non required inputs that are not set are returned as None
    Returns:
        Dict[str, Any]: [description]
    """
    parsed_inputs = dict()
    for input_name, input_config in INPUTS.items():
        this_input_value = actions_toolkit.get_input(
            input_name,
            required=input_config.get("required", input_config.get("default", None) is None),
        )
        parsed_inputs[input_name] = this_input_value if this_input_value != "" else None
        # set defaults if not running in github, this is to ease local testing
        # https://docs.github.com/en/actions/learn-github-actions/environment-variables
        if (
            os.environ.get("CI", "false").lower() == "false"
            and os.environ.get("GITHUB_ACTIONS", "false").lower() == "false"
        ):
            if parsed_inputs[input_name] is None:
                parsed_inputs[input_name] = input_config.get("default", None)
                if parsed_inputs[input_name] is None:
                    actions_toolkit.set_failed(f"Error getting inputs. {input_name} is missing a default")
    return validate_inputs(parsed_inputs)


def validate_inputs(parsed_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate inputs
    Args:
        inputs (Dict[str, Any]): [description]
    """
    if parsed_inputs["action"] not in VALID_ACTIONS:
        actions_toolkit.set_failed(f"Invalid action: {parsed_inputs['action']}")
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
                "Error getting inputs. repo is 'self' and GITHUB_REPOSITORY env var is not set. Please set INPUT_REPO or GITHUB_REPOSITORY in the env"
            )

    try:
        repo = get_github_client(parsed_inputs["token"]).get_repo(parsed_inputs["repo"])
    except Exception as exc:  # this should be tighter
        actions_toolkit.set_failed(f"Error while retriving {parsed_inputs['repo']} from Github. {exc}")

    parsed_inputs["repo_object"] = repo

    return parsed_inputs


def attr_to_kwarg(attr_name: str, obj: Any, kwargs: dict, transform_key: str = None):
    value = getattr(obj, attr_name, None)
    if value is not None:
        if transform_key is None:
            kwargs[attr_name] = value
        else:
            kwargs[transform_key] = value
