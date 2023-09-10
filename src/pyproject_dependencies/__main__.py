"""Print Requires-Dist metadata of a set of python projects."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

from build import BuildBackendException
from build.util import project_wheel_metadata
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def subprocess_runner(
    cmd: Sequence[str],
    cwd: str | None = None,
    extra_environ: Mapping[str, str] | None = None,
) -> None:
    """Run a subprocess and print its output on stderr in case of error only."""
    env = os.environ.copy()
    if extra_environ:
        env.update(extra_environ)

    res = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if res.returncode != 0:
        sys.stderr.write(res.stdout.decode("utf-8", errors="replace"))
        raise subprocess.CalledProcessError(res.returncode, cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "projects",
        metavar="PROJECT",
        nargs="*",
        help="project directory or pyproject.toml or setup.py",
    )
    parser.add_argument(
        "--no-isolation",
        action="store_true",
        help=(
            "whether or not to invoke the build backend "
            "in the current environment or "
            "to create an isolated one and invoke it there"
        ),
    )
    parser.add_argument(
        "--no-exclude-self",
        action="store_true",
        help=(
            "whether or not to exclude the projects themselves from the output, "
            "when they depend on each other"
        ),
    )
    parser.add_argument(
        "--ignore-build-errors",
        action="store_true",
    )
    parser.add_argument(
        "--name-filter",
        dest="name_filters",
        action="append",
        metavar="REGEX",
        help="filter out dependencies whose canonical name matches a regex",
    )
    # parse and pre-process arguments and options
    args = parser.parse_args()
    project_paths = []
    for project in args.projects:
        project_path = Path(project)
        if project_path.is_dir() and (
            project_path.joinpath("setup.py").is_file()
            or project_path.joinpath("pyproject.toml").is_file()
        ):
            project_paths.append(project_path)
        elif project_path.is_file() and project_path.name in (
            "setup.py",
            "pyproject.toml",
        ):
            project_paths.append(project_path.parent)
    name_filters_re = []
    for name_filter in args.name_filters or []:
        name_filters_re.append(re.compile(name_filter))
    # ask the build backend to prepare metadata for each projects
    metadata_by_project_name = {}
    for project_path in project_paths:
        try:
            project_metadata = project_wheel_metadata(
                project_path,
                not args.no_isolation,
                runner=subprocess_runner,
            )
        except BuildBackendException as e:
            if args.ignore_build_errors:
                print(
                    f"Warning: ignoring build error in {project_path.resolve()}: {e}",
                    file=sys.stderr,
                )
                continue
            else:
                print(
                    f"Error: build error in {project_path.resolve()}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        project_name = canonicalize_name(project_metadata["Name"])
        if project_name in metadata_by_project_name:
            print(
                f"Warning: {project_name} already seen, "
                f"ignoring {project_path.resolve()}",
                file=sys.stderr,
            )
            continue
        metadata_by_project_name[project_name] = project_metadata
    # filter
    deps = set()
    for project_metadata in metadata_by_project_name.values():
        for dep in project_metadata.get_all("Requires-Dist", []):
            req = Requirement(dep)
            req_name = canonicalize_name(req.name)
            if not args.no_exclude_self and req_name in metadata_by_project_name:
                continue
            if any(filter.match(req_name) for filter in name_filters_re):
                continue
            deps.add(dep)
    # print
    for dep in sorted(deps):
        print(dep)


if __name__ == "__main__":
    main()
