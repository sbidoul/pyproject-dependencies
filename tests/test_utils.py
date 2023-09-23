import pytest

from pyproject_dependencies.__main__ import _dep_has_extra


@pytest.mark.parametrize(
    ("dep", "expected"),
    [
        ("stuff", False),
        ("stuff[extra]", False),
        ("stuff==1.0", False),
        ("extra==1.0", False),
        ("stuff>=1; extra == 'test'", True),
    ],
)
def test_dep_has_extras(dep: str, expected: bool) -> None:
    assert _dep_has_extra(dep) is expected
