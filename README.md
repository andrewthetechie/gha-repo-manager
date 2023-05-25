# Repo Manager via Github Actions
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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
* Files

See [examples/settings.yml](./examples/settings.yml) for an example config file. The schemas for this file are in [repo_manager.schemas](./repo_magager/schemas).

### File Management -- Experimental

File management can copy files from your local environment to a target repo, copy files from one location to another in the target repo, move files in the target repo, and delete files in the target repo.

File operations are performed using the Github BLOB API and your PAT. Each file operation is a separate commit.

This feature is helpful to keep workflows or settings file in sync from a central repo to many repos.

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
| github_server_url | Set a custom github server url for github api operations. Useful if you're running on GHE. Will try to autodiscover from env.GITHUB_SERVER_URL if left at default | `false` | none |
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

## Contributors

Please see our [Contribution Guide](./CONTRIBUTING.md) for more info on how you can contribute. All contributors and participants in this repo must follow our [Code of Conduct](./CODE_OF_CONDUCT.md).
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/andrewthetechie"><img src="https://avatars.githubusercontent.com/u/1377314?v=4?s=100" width="100px;" alt="Andrew"/><br /><sub><b>Andrew</b></sub></a><br /><a href="#ideas-andrewthetechie" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/andrewthetechie/gha-repo-manager/commits?author=andrewthetechie" title="Tests">⚠️</a> <a href="https://github.com/andrewthetechie/gha-repo-manager/commits?author=andrewthetechie" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/actuarysailor"><img src="https://avatars.githubusercontent.com/u/24359398?v=4?s=100" width="100px;" alt="shiro"/><br /><sub><b>shiro</b></sub></a><br /><a href="https://github.com/andrewthetechie/gha-repo-manager/issues?q=author%3Aactuarysailor" title="Bug reports">🐛</a> <a href="https://github.com/andrewthetechie/gha-repo-manager/commits?author=actuarysailor" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
