import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Union


def _make_project(
    tmp_path: Path,
    name: str,
    deps: List[str],
    optional_dep: Union[Dict[str, List[str]], None] = None,
) -> None:
    assert len(deps) > 0
    project_path = tmp_path / name
    project_path.mkdir()
    pyproject_toml = project_path / "pyproject.toml"
    deps_str = '", "'.join(deps)
    pyproject = textwrap.dedent(
        f"""
            [project]
            name = "{name}"
            version = "1.0"
            dependencies = ["{deps_str}"]
        """
    )
    if optional_dep is not None:
        assert len(optional_dep) == 1
        optional_dep_name, optional_dep_deps = next(iter(optional_dep.items()))
        optional_dep_deps_str = '", "'.join(optional_dep_deps)
        pyproject += textwrap.dedent(
            f"""
                [project.optional-dependencies]
                {optional_dep_name} = ["{optional_dep_deps_str}"]
            """
        )
    pyproject_toml.write_text(pyproject)


def _make_legacy_project(tmp_path: Path, name: str, deps: List[str]) -> None:
    assert len(deps) > 0
    project_path = tmp_path / name
    project_path.mkdir()
    setup_py = project_path / "setup.py"
    deps_str = '", "'.join(deps)
    setup_py.write_text(
        textwrap.dedent(
            f"""
            from setuptools import setup

            setup(
                name="{name}",
                version="1.0",
                install_requires=["{deps_str}"],
            )
            """
        )
    )


def test_basic(tmp_path: Path) -> None:
    _make_project(tmp_path, name="p1", deps=["d1", "d2"])
    _make_project(tmp_path, name="p2", deps=["d1", "d3", "p1"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyproject_dependencies",
            str(tmp_path / "p1"),
            str(tmp_path / "p2" / "pyproject.toml"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == "d1\nd2\nd3\n"


def test_basic_legacy(tmp_path: Path) -> None:
    _make_legacy_project(tmp_path, name="p1", deps=["d1", "d2"])
    _make_legacy_project(tmp_path, name="p2", deps=["d1", "d3", "p1"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyproject_dependencies",
            str(tmp_path / "p1"),
            str(tmp_path / "p2" / "setup.py"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == "d1\nd2\nd3\n"


def test_name_filter(tmp_path: Path) -> None:
    _make_project(tmp_path, name="p1", deps=["D1", "d2"])
    _make_project(tmp_path, name="p2", deps=["d1", "d3", "p1"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyproject_dependencies",
            "--name-filter=^d1$",
            str(tmp_path / "p1"),
            str(tmp_path / "p2" / "pyproject.toml"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == "d2\nd3\n"


def test_exclude_self(tmp_path: Path) -> None:
    _make_project(tmp_path, name="p1", deps=["d1", "d2"])
    _make_project(tmp_path, name="p2", deps=["d1", "d3", "p1"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyproject_dependencies",
            "--no-exclude-self",
            str(tmp_path / "p1"),
            str(tmp_path / "p2" / "pyproject.toml"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == "d1\nd2\nd3\np1\n"


def test_extras_ignored(tmp_path: Path) -> None:
    _make_project(tmp_path, name="p1", deps=["d1", "d2"], optional_dep={"test": ["d3"]})
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyproject_dependencies",
            "--no-exclude-self",
            str(tmp_path / "p1"),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout == "d1\nd2\n"
