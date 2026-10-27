"""Tests for the bundled example filters (masha/filters) and tests (masha/tests)."""

from pathlib import Path

import pytest

from masha.filters.string_utils import lowercase, uppercase
from masha.template_renderer import load_functions_from_directory

# Imported as a module: a bare ``test_is_even`` name would be collected
# by pytest as a test function.
from masha.tests import maths_utils

pkg_dir = Path(__file__).parent.parent / "masha"


class TestStringFilters:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("abc", "ABC"), ("MiXeD 1", "MIXED 1"), ("", "")],
    )
    def test_uppercase(self, value, expected):
        assert uppercase(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("ABC", "abc"), ("MiXeD 1", "mixed 1"), ("", "")],
    )
    def test_lowercase(self, value, expected):
        assert lowercase(value) == expected

    def test_directory_exposes_filters(self):
        assert set(load_functions_from_directory(pkg_dir / "filters")) == {
            "lowercase",
            "uppercase",
        }


class TestMathsTests:
    @pytest.mark.parametrize(
        ("number", "expected"), [(0, True), (2, True), (3, False), (-4, True)]
    )
    def test_is_even(self, number, expected):
        assert maths_utils.is_even(number) is expected
        assert maths_utils.test_is_even(number) is expected

    def test_directory_exposes_tests(self):
        assert set(load_functions_from_directory(pkg_dir / "tests")) == {
            "is_even",
            "test_is_even",
        }
