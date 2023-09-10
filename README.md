# pyproject-dependencies

    usage: pyproject-dependencies [-h] [--no-isolated] [--no-exclude-self] [--ignore-build-errors] [--name-filter REGEX] [PROJECT ...]

    Print Requires-Dist metadata of a set of python projects.

    positional arguments:
    PROJECT               project directory or pyproject.toml or setup.py

    options:
    -h, --help            show this help message and exit
    --no-isolation        whether or not to invoke the build backend in the current environment or to create an isolated one and invoke it there
    --no-exclude-self     whether or not to exclude the projects themselves from the output, when they depend on each other
    --ignore-build-errors
    --name-filter REGEX   filter out dependencies whose canonical name matches a regex
