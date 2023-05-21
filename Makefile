.DEFAULT_GOAL := help

# This help function will automatically generate help/usage text for any make target that is commented with "##".
# Targets with a singe "#" description do not show up in the help text
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'


build: ## build a docker image locally
	docker build -t gha-repo-manager -f Dockerfile .

generate-inputs: ## Generate a dict of inputs from actions.yml into repo_manager/utils/__init__.py
	./.github/scripts/replace_inputs.sh
