import json
import sys

from actions_toolkit import core as actions_toolkit
from pydantic import ValidationError
from yaml import YAMLError

from repo_manager.gh import GithubException, UnknownObjectException
from repo_manager.gh.branch_protections import check_repo_branch_protections
from repo_manager.gh.branch_protections import update_branch_protection
from repo_manager.gh.files import copy_file
from repo_manager.gh.files import delete_file
from repo_manager.gh.files import move_file
from repo_manager.gh.files import RemoteSrcNotFoundError
from repo_manager.gh.labels import check_repo_labels
from repo_manager.gh.labels import update_label
from repo_manager.gh.secrets import check_repo_secrets
from repo_manager.gh.secrets import create_secret
from repo_manager.gh.secrets import delete_secret
from repo_manager.gh.settings import check_repo_settings
from repo_manager.gh.settings import update_settings
from repo_manager.schemas import load_config
from repo_manager.utils import get_inputs


def main():  # noqa: C901
    try:
        inputs = get_inputs()
    # actions toolkit has very broad exceptions :(
    except Exception as exc:
        actions_toolkit.set_failed(f"Unable to collect inputs {exc}")
    actions_toolkit.debug(f"Loading config from {inputs['settings_file']}")
    try:
        config = load_config(inputs["settings_file"])
    except FileNotFoundError:
        actions_toolkit.set_failed(f"{inputs['settings_file']} does not exist or is not readable")
    except YAMLError as exc:
        actions_toolkit.set_failed(f"Unable to read {inputs['settings_file']} - {exc}")
    except ValidationError as exc:
        actions_toolkit.set_failed(f"{inputs['settings_file']} is invalid - {exc}")

    actions_toolkit.debug(f"Inputs: {inputs}")
    if inputs["action"] == "validate":
        actions_toolkit.set_output("result", f"Validated {inputs['settings_file']}")
        actions_toolkit.debug(json_diff := json.dumps({}))
        actions_toolkit.set_output("diff", json_diff)
        sys.exit(0)
    actions_toolkit.info(f"Config from {inputs['settings_file']} validated.")

    check_result = True
    diffs = {}
    for check, to_check in {
        check_repo_settings: ("settings", config.settings),
        check_repo_secrets: ("secrets", config.secrets),
        check_repo_labels: ("labels", config.labels),
        check_repo_branch_protections: (
            "branch_protections",
            config.branch_protections,
        ),
    }.items():
        check_name, to_check = to_check
        if to_check is not None:
            this_check, this_diffs = check(inputs["repo_object"], to_check)
            check_result &= this_check
            if this_diffs is not None:
                diffs[check_name] = this_diffs

    actions_toolkit.debug(json_diff := json.dumps(diffs))
    actions_toolkit.set_output("diff", json_diff)

    if inputs["action"] == "check":
        if not check_result:
            actions_toolkit.set_output("result", "Check failed, diff detected")
            actions_toolkit.set_failed("Diff detected")
        actions_toolkit.set_output("result", "Check passed")
        sys.exit(0)

    if inputs["action"] == "apply":
        errors = []

        # Because we cannot diff secrets, just apply it every time
        if config.secrets is not None:
            for secret in config.secrets:
                if secret.exists:
                    try:
                        create_secret(
                            inputs["repo_object"], secret.key, secret.expected_value, secret.type == "dependabot"
                        )
                        actions_toolkit.info(f"Set {secret.key} to expected value")
                    except Exception as exc:  # this should be tighter
                        errors.append(
                            {
                                "type": "secret-update",
                                "key": secret.key,
                                "error": f"{exc}",
                            }
                        )
                else:
                    try:
                        delete_secret(inputs["repo_object"], secret.key, secret.type == "dependabot")
                        actions_toolkit.info(f"Deleted {secret.key}")
                    except Exception as exc:  # this should be tighter
                        errors.append(
                            {
                                "type": "secret-delete",
                                "key": secret.key,
                                "error": f"{exc}",
                            }
                        )

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
                            label_object.expected_name,
                            label_object.color_no_hash,
                            label_object.description,
                        )
                        actions_toolkit.info(f"Created label {label_name}")
                    except Exception as exc:  # this should be tighter
                        errors.append(
                            {
                                "type": "label-create",
                                "name": label_name,
                                "error": f"{exc}",
                            }
                        )
            for label_name in labels_diff["diffs"].keys():
                update_label(inputs["repo_object"], config.labels_dict[label_name])
                actions_toolkit.info(f"Updated label {label_name}")

        bp_diff = diffs.get("branch_protections", None)
        if bp_diff is not None:
            # delete branch protection
            for branch_name in bp_diff["extra"]:
                try:
                    this_branch = inputs["repo_object"].get_branch(branch_name)
                    this_branch.remove_protection()
                except GithubException as ghexc:
                    if ghexc.status != 404:
                        # a 404 on a delete is fine, means it isnt protected
                        errors.append(
                            {
                                "type": "bp-delete",
                                "name": branch_name,
                                "error": f"{ghexc}",
                            }
                        )
                except Exception as exc:  # this should be tighter
                    errors.append({"type": "bp-delete", "name": branch_name, "error": f"{exc}"})

            # update or create branch protection
            for branch_name in bp_diff["missing"] + list(bp_diff["diffs"].keys()):
                try:
                    bp_config = config.branch_protections_dict[branch_name]
                    if bp_config.protection is not None:
                        update_branch_protection(inputs["repo_object"], branch_name, bp_config.protection)
                        actions_toolkit.info(f"Updated branch proection for {branch_name}")
                    else:
                        actions_toolkit.warning(f"Branch protection config for {branch_name} is empty")
                except GithubException as ghexc:
                    if ghexc.status == 404:
                        actions_toolkit.info(
                            f"Can't Update branch protection for {branch_name} because the branch does not exist"
                        )
                    else:
                        errors.append(
                            {
                                "type": "bp-update",
                                "name": branch_name,
                                "error": f"{ghexc}",
                            }
                        )
                except Exception as exc:  # this should be tighter
                    errors.append({"type": "bp-update", "name": branch_name, "error": f"{exc}"})

        if config.settings is not None:
            try:
                update_settings(inputs["repo_object"], config.settings)
                actions_toolkit.info("Synced Settings")
            except Exception as exc:
                errors.append({"type": "settings-update", "error": f"{exc}"})

        commits = []
        if config.files is not None:
            for file_config in config.files:
                # delete files
                if not file_config.exists:
                    try:
                        commits.append(delete_file(inputs["repo_object"], file_config))
                        actions_toolkit.info(f"Deleted {str(file_config.dest_file)}")
                    except UnknownObjectException:
                        target_branch = (
                            file_config.target_branch
                            if file_config.target_branch is not None
                            else inputs["repo_object"].default_branch
                        )
                        actions_toolkit.warning(
                            f"{str(file_config.dest_file)} does not exist in "
                            + f"{target_branch}"
                            + " branch. Because this is a delete, not failing run"
                        )
                    except Exception as exc:
                        errors.append({"type": "file-delete", "file": str(file_config.dest_file), "error": f"{exc}"})
                elif file_config.move:
                    try:
                        copy_commit, delete_commit = move_file(inputs["repo_object"], file_config)
                        commits.append(copy_commit)
                        commits.append(delete_commit)
                        actions_toolkit.info(f"Moved {str(file_config.src_file)} to {str(file_config.dest_file)}")
                    except RemoteSrcNotFoundError:
                        target_branch = (
                            file_config.target_branch
                            if file_config.target_branch is not None
                            else inputs["repo_object"].default_branch
                        )
                        actions_toolkit.warning(
                            f"{str(file_config.src_file)} does not exist in "
                            + f"{target_branch}"
                            + " branch. Because this is a move, not failing run"
                        )
                    except Exception as exc:
                        errors.append(
                            {
                                "type": "file-move",
                                "src_file": str(file_config.src_file),
                                "dest_file": str(file_config.dest_file),
                                "error": f"{exc}",
                            }
                        )
                else:
                    try:
                        commits.append(copy_file(inputs["repo_object"], file_config))
                        actions_toolkit.info(
                            f"Copied{' remote ' if file_config.remote_src else ' '}{str(file_config.src_file)}"
                            + f" to {str(file_config.dest_file)}"
                        )
                    except Exception as exc:
                        errors.append(
                            {
                                "type": "file-copy",
                                "src_file": str(file_config.src_file),
                                "dest_file": str(file_config.dest_file),
                                "error": f"{exc}",
                            }
                        )
        actions_toolkit.info("Commit SHAs: " + ",".join(commits))

        if len(errors) > 0:
            actions_toolkit.error(json.dumps(errors))
            actions_toolkit.set_failed("Errors during apply")
        actions_toolkit.set_output("result", "Apply successful")


if __name__ == "__main__":
    main()
