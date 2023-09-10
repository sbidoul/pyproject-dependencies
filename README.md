# pyproject-dependencies

Print dependencies of a set of python projects.

    usage: __main__.py [-h] [--isolated] [--include-self] [--ignore-build-errors] [--name-filter REGEX] [PROJECT [PROJECT ...]]

    Print Requires-Dist metadata for python projects.

    positional arguments:
    PROJECT               project directory or pyproject.toml or setup.py

    optional arguments:
    -h, --help            show this help message and exit
    --isolated            whether or not to invoke the build backend in the current environment or to create an isolated one and invoke it there
    --include-self        whether or not to include the projects themselves in the output
    --ignore-build-errors
    --name-filter REGEX   filter out dependencies whose canonical name matches a regex
