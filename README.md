# pyproject-dependencies

![PyPI - Version](https://img.shields.io/pypi/v/pyproject-dependencies?logo=pypi&logoColor=gold)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyproject-dependencies?logo=python&logoColor=gold)

This tool leverages the Python standard build backend interface (via the
[build](https://pypi.org/project/build) library) in order to compute and print the
direct dependencies of a set of python projects.

    usage: pyproject-dependencies [-h] [--no-isolation] [--no-exclude-self] [--ignore-build-errors] [--name-filter REGEX] [PROJECT ...]

    Print direct dependencies of a set of python projects.

    positional arguments:
      PROJECT               project directory or pyproject.toml or setup.py

    options:
      -h, --help            show this help message and exit
      --no-isolation        whether or not to invoke the build backend in the current environment or to create an isolated one and invoke it there
      --no-exclude-self     whether or not to exclude the projects themselves from the output, when they depend on each other
      --ignore-build-errors
      --name-filter REGEX   filter out dependencies whose canonical name matches a regex
