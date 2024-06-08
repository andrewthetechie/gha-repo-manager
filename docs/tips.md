# Create virtual environment

- Follow [Visual Studio Code instructions to create a virtual environment](https://code.visualstudio.com/docs/python/environments#_creating-environments)
- Choose the `Venv` option
- Run the script below:

```
.venv\Scripts\activate
pip install Annotated
pip install pydantic
pip install pydantic_extra_types
pip install pygithub
pip install actions-toolkit
pip install pyyaml
```

# Spoof Environment Variables from GitHub Agent

Create a `.env` file in your root-directory of the repo (this repo)

```
INPUT_GITHUB_SERVER_URL=none
INPUT_REPO=self
INPUT_TOKEN=********
INPUT_ACTION=check
INPUT_SETTINGS_FILE=./.github/settings.yml
```

# Create a Python test file for debugging

Create a `test.py` file in your root-directory of the repo (this repo)

```
from repo_manager.main import main

main()
```
