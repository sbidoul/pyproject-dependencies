"""Print direct dependencies of a set of python projects."""

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from build.util import project_wheel_metadata
from packaging.requirements import Requirement
from packaging.utils import NormalizedName, canonicalize_name

from .compat import tomllib

extra_marker_re = re.compile(r".+extra\s*==")


def _dep_has_extra(dep: str) -> bool:
    return bool(extra_marker_re.match(dep))


def subprocess_runner(
    cmd: Sequence[str],
    cwd: Optional[str] = None,
    extra_environ: Optional[Mapping[str, str]] = None,
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


class InvalidPyproject(RuntimeError):
    pass


def _validate_pyproject(project: Dict[str, Any]) -> None:
    if "name" not in project:
        raise InvalidPyproject("Missing 'name' key")
    dynamic = project.get("dynamic", [])
    if "dependencies" in dynamic and "dependencies" in project:
        raise InvalidPyproject(
            "'dependencies' key cannot be set while declared as 'dynamic'"
        )


@dataclass
class BasicPackageMetadata:
    name: NormalizedName
    dependencies: List[str]


def metadata_from_pyproject(
    project_path: Path,
) -> Union[BasicPackageMetadata, None]:
    """Obtain metadata for a project using pyproject.toml.

    Return None if the dependencies are not static or if the project does not use
    pyproject.toml.
    """
    pyproject_path = project_path / "pyproject.toml"
    if not pyproject_path.is_file():
        # no pyproject.toml, need to use the default build backend
        return None
    parsed_pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = parsed_pyproject.get("project")
    if not project:
        # no project table, need to use build backend
        return None
    _validate_pyproject(project)
    if "dependencies" in project.get("dynamic", []):
        # dynamic dependencies, need to use build backend
        return None
    return BasicPackageMetadata(
        name=canonicalize_name(project["name"]),
        dependencies=project.get("dependencies", []),
    )


def metadata_from_build_backend(
    project_path: Path, isolated: bool
) -> BasicPackageMetadata:
    metadata = project_wheel_metadata(
        project_path,
        isolated,
        runner=subprocess_runner,
    )
    requires_dist = metadata.get_all("Requires-Dist", [])
    dependencies = [dep for dep in requires_dist if not _dep_has_extra(dep)]
    return BasicPackageMetadata(
        name=canonicalize_name(metadata["Name"]), dependencies=dependencies
    )


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
    # obtain the metadata we need for each projects
    metadata_by_project_name = {}
    for project_path in project_paths:
        try:
            project_metadata = metadata_from_pyproject(
                project_path
            ) or metadata_from_build_backend(
                project_path,
                not args.no_isolation,
            )
        except Exception as e:
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
        if project_metadata.name in metadata_by_project_name:
            print(
                f"Warning: {project_metadata.name} already seen, "
                f"ignoring {project_path.resolve()}",
                file=sys.stderr,
            )
            continue
        metadata_by_project_name[project_metadata.name] = project_metadata
    # filter
    deps = set()
    for project_metadata in metadata_by_project_name.values():
        for dep in project_metadata.dependencies:
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
