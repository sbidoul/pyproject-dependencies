import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List


def _make_project(tmp_path: Path, name: str, deps: List[str]) -> None:
    assert len(deps) > 0
    project_path = tmp_path / name
    project_path.mkdir()
    pyproject_toml = project_path / "pyproject.toml"
    deps_str = '", "'.join(deps)
    pyproject_toml.write_text(
        textwrap.dedent(
            f"""
            [project]
            name = "{name}"
            version = "1.0"
            dependencies = ["{deps_str}"]
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
