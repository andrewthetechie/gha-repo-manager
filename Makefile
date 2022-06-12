.DEFAULT_GOAL := help

# This help function will automatically generate help/usage text for any make target that is commented with "##".
# Targets with a singe "#" description do not show up in the help text
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

setup-dev:  pyenv-install pyenv-setup install-requirements setup-pre-commit ## Uses pyenv to setup a virtualenv and install requirements

pyenv-install:
	pyenv install 3.9.2

pyenv-setup:
	pyenv virtualenv 3.9.2 gha-repo-manager
	pyenv local gha-repo-manager

install-requirements:  ## Pip installs our requirements
	pip install -r Docker/builder/rootfs/requirements.txt
	pip install -r requirements-dev.txt

setup-pre-commit:
	pre-commit install

build:
	docker build --platform linux/amd64 -t gha-repo-manager -f Docker/Dockerfile .
