# Local Requirements

- Docker
- python 3.9.2 environment (makefile can use pyenv to set this up for you, make setup-dev)
- actionlint

# Local Setup

```
setup-dev
```

## Actionlint

To install actionlint you can either run go locally and run `make install-actionlint` or if you are on a mac, you can install it with `brew install actionlint`.

# Building locally

```
make build
```

# Releasing

Use the release job https://github.com/andrewthetechie/gha-repo-manager/actions/workflows/release.yml

Specify an incremented version, job will fail if you repeat a release.

Fill in any release notes

After the job runs, edit the Release in the github ui and check the box to release it to Github Actions Marketplace and click Update Release.
