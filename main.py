import json
import os
import sys

from actions_toolkit import core as actions_toolkit

from repo_manager.github.branch_protections import check_repo_branch_protections
from repo_manager.github.branch_protections import update_branch_protection
from repo_manager.github.labels import check_repo_labels
from repo_manager.github.labels import update_label
from repo_manager.github.secrets import check_repo_secrets
from repo_manager.github.secrets import upsert_secret
from repo_manager.github.settings import check_repo_settings
from repo_manager.github.settings import update_setting
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
        errors = []
        from pprint import pprint

        pprint(diffs)

        # Because we cannot diff secrets, just apply it every time
        for secret in config.secrets:
            if secret.exists:
                try:
                    inputs["repo_object"].create_secret(secret.key, secret.expected_value)
                    actions_toolkit.info(f"Set {secret.key} to expected value")
                except Exception as exc:  # this should be tighter
                    errors.append({"type": "secret-update", "key": secret.key, "error": f"{exc}"})
            else:
                try:
                    inputs["repo_object"].delete_secret(secret.key)
                    actions_toolkit.info(f"Deleted {secret.key}")
                except Exception as exc:  # this should be tighter
                    errors.append({"type": "secret-delete", "key": secret.key, "error": f"{exc}"})

        labels_diff = diffs.get("labels", None)
        if labels_diff is not None:
            for label_name in labels_diff["extra"]:
                try:
                    this_label = inputs["repo_object"].get_label(label_name)
                    this_label.delete()
                    actions_toolkit.info(f"Deleted {label_name}")
                except Exception as exc:  # this should be tighter
                    errors.append({"type": "label-delete", "name": label_name, "error": f"{exc}"})
            for label_name in labels_diff["missing"]:
                label_object = config.labels_dict[label_name]
                if label_object.name != label_object.expected_name:
                    update_label(inputs["repo_object"], label_object)
                    actions_toolkit.info(f"Renamed {label_object.name} to {label_object.expected_name}")
                else:
                    try:
                        inputs["repo_object"].create_label(
                            label_object.expected_name, label_object.color_no_hash, label_object.description
                        )
                        actions_toolkit.info(f"Created label {label_name}")
                    except Exception as exc:  # this should be tighter
                        errors.append({"type": "label-create", "name": label_name, "error": f"{exc}"})
            for label_name in labels_diff["diffs"].keys():
                update_label(inputs["repo_object"], config.labels_dict[label_name])
                actions_toolkit.info(f"Updated label {label_name}")
        if len(errors) > 0:
            actions_toolkit.error(json.dumps(errors))
            actions_toolkit.set_failed("Errors during apply")
        actions_toolkit.set_output("result", "Apply successful")


if __name__ == "__main__":
    main()
