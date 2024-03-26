import json
from pathlib import Path


def edit_cruft():
    """
    A hackish way to get around Azure DevOps permissions limitations.
    After the cookiecutter repo is cloned locally, the .cruft.json file
    points to the file path of the cookiecutter. This is due to the very
    restrictive way Azure DevOps handles repo checkouts.
    """
    cookiecutter_path = Path("..") / "app-library-template"

    with open(".cruft.json", "r") as fstream:
        data = json.load(fstream)
        data["template"] = str(cookiecutter_path)
        data["context"]["cookiecutter"]["_template"] = str(cookiecutter_path)

    with open(".cruft.json", "w") as fstream:
        json.dump(data, fstream, indent=2)


if __name__ == "__main__":
    edit_cruft()
