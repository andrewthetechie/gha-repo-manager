import json
import os
import sys

from actions_toolkit import core as actions_toolkit

from repo_manager.github.branch_protections import check_repo_branch_protections
from repo_manager.github.labels import check_repo_labels
from repo_manager.github.secrets import check_repo_secrets
from repo_manager.github.settings import check_repo_settings
from repo_manager.schemas import load_config
from repo_manager.utils import get_inputs


def main():
    inputs = get_inputs()
    actions_toolkit.debug(f"Loading config from {inputs['settings_file']}")
    config = load_config(inputs["settings_file"])

    if inputs["action"] == "validate":
        actions_toolkit.set_output("result", f"Validated {inputs['settings_file']}")
        actions_toolkit.set_output("diff", json.dumps({}))
        sys.exit(0)
    actions_toolkit.info(f"Config from {inputs['settings_file']} validated.")

    check_result = True
    diffs = {}
    for check, to_check in {
        check_repo_settings: ("settings", config.settings),
        check_repo_secrets: ("secrets", config.secrets),
        check_repo_labels: ("labels", config.labels),
        check_repo_branch_protections: ("branch_protections", config.branch_protections),
    }.items():
        check_name, to_check = to_check
        if to_check is not None:
            this_check, this_diffs = check(inputs["repo_object"], to_check)
            check_result &= this_check
            diffs[check_name] = this_diffs

        actions_toolkit.set_output("diff", json.dumps(diffs))

    if inputs["action"] == "check":
        if not check_result:
            actions_toolkit.set_output("result", "Check failed, diff detected")
            actions_toolkit.set_failed("Diff detected")
        actions_toolkit.set_output("result", "Check passed")
        sys.exit(0)

    if inputs["action"] == "apply":
        actions_toolkit.set_failed("Not Yet Implemented")


if __name__ == "__main__":
    main()
