# Repo Manager via Github Actions

[![Action Template](https://img.shields.io/badge/Action%20Template-Python%20Container%20Action-blue.svg?colorA=24292e&colorB=0366d6&style=flat&longCache=true&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6wAADOsB5dZE0gAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAERSURBVCiRhZG/SsMxFEZPfsVJ61jbxaF0cRQRcRJ9hlYn30IHN/+9iquDCOIsblIrOjqKgy5aKoJQj4O3EEtbPwhJbr6Te28CmdSKeqzeqr0YbfVIrTBKakvtOl5dtTkK+v4HfA9PEyBFCY9AGVgCBLaBp1jPAyfAJ/AAdIEG0dNAiyP7+K1qIfMdonZic6+WJoBJvQlvuwDqcXadUuqPA1NKAlexbRTAIMvMOCjTbMwl1LtI/6KWJ5Q6rT6Ht1MA58AX8Apcqqt5r2qhrgAXQC3CZ6i1+KMd9TRu3MvA3aH/fFPnBodb6oe6HM8+lYHrGdRXW8M9bMZtPXUji69lmf5Cmamq7quNLFZXD9Rq7v0Bpc1o/tp0fisAAAAASUVORK5CYII=)](https://github.com/andrewthetechie/gha-repo-manager)
[![Actions Status](https://github.com/andrewthetechie/gha-repo-manager/workflows/Lint/badge.svg)](https://github.com/andrewthetechie/gha-repo-manager/actions)
[![Actions Status](https://github.com/andrewthetechie/gha-repo-manager/workflows/Integration%20Test/badge.svg)](https://github.com/andrewthetechie/gha-repo-manager/actions)

<!-- action-docs-description -->
## Description

Manage your Github repo(s) settings and secrets using Github Actions and a yaml file


<!-- action-docs-description -->

## Usage
This action manages your repo from a yaml file. You can manage:
* branch protection
* labels
* repos
* secrets
* repo settings

See [examples/settings.yml](./examples/settings.yml) for an example config file. The schemas for this file are in [repo_manager.schemas](./repo_magager/schemas).
### Example workflow

```yaml
name: Run Repo Manager
on: [workflow_dispatch]
jobs:
  repo-manager:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    name: Checkout
    - name: Run RepoManager
      uses: andrewthetechie/gha-repo-manager@main
      with:
        # Apply your settings to the repo, can also be check to just check repo settings vs your file or validate, to validate your
        # file is valid
        action: apply
        settings_file: .github/settings.yml
        # need a PAT that can edit repo settings
        token: ${{ secrets.GITHUB_PAT }}

```


<!-- action-docs-inputs -->
## Inputs

| parameter | description | required | default |
| - | - | - | - |
| action | What action to take with this action. One of validate, check, or apply. Validate will validate your settings file, but not touch your repo. Check will check your repo with your settings file and output a report of any drift. Apply will apply the settings in your settings file to your repo | `false` | check |
| settings_file | What yaml file to use as your settings. This is local to runner running this action. | `false` | .github/settings.yml |
| repo | What repo to perform this action on. Default is self, as in the repo this action is running in | `false` | self |
| token | What github token to use with this action. | `true` |  |



<!-- action-docs-inputs -->

<!-- action-docs-outputs -->
## Outputs

| parameter | description |
| - | - |
| result | Result of the action |
| diff | Diff of this action, dumped to a json string |



<!-- action-docs-outputs -->

<!-- action-docs-runs -->
## Runs

This action is a `docker` action.


<!-- action-docs-runs -->
