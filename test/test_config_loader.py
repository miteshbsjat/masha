import sys
from pathlib import Path

import pytest
import yaml
from returns.result import Failure, Success

# directory reach
directory = Path(__file__).parent.parent / "masha"
sys.path.append(str(directory))
from config_loader import merge_configs, load_and_merge_configs

test_dir = Path(__file__).parent


class TestMergeConfigs:
    def test_empty_configs(self):
        result = merge_configs({})
        assert result == {}

    def test_single_config(self):
        config1 = {"a": 1, "b": 2}
        config2 = {"a": 3}
        expected = {"a": 3, "b": 2}
        result = merge_configs([config1, config2])
        assert result == expected

    def test_multiple_configs_no_overlap(self):
        config1 = {"a": 1, "b": 2}
        config2 = {"c": 3, "d": 4}
        result = merge_configs([config1, config2])
        assert result == {"a": 1, "b": 2, "c": 3, "d": 4}

    def test_multiple_configs_with_overlap(self):
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 3, "c": 4}
        result = merge_configs([config1, config2])
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_configs(self):
        config1 = {"a": {"x": 1}, "b": 2}
        config2 = {"a": {"y": 2}, "c": 3}
        result = merge_configs([config1, config2])
        assert result == {"a": {"y": 2}, "b": 2, "c": 3}

    def test_empty_file_skipped(self):
        config_paths = test_dir / "config-d.yaml"
        result = load_and_merge_configs([config_paths])
        assert isinstance(result, Success)
        assert result.unwrap() == {}


class TestLoadAndMergeConfigs:
    def test_happy_path(self):
        config_paths = test_dir / "config1.yaml"
        result = load_and_merge_configs([config_paths])
        assert isinstance(result, Success)
        assert result.unwrap() == {
             "keya": "vala",
             "keyb": "val2",
             "keyc": {"keyca": "valca"},
         }

    def test_happy_multiple_paths(self):
        config_path1 = test_dir / "config1.yaml"
        config_path2 = test_dir / "config2.json"
        result = load_and_merge_configs([config_path1, config_path2])
        assert isinstance(result, Success)
        assert result.unwrap() == {
             "keya": "vala",
             "keyb": "valb_json",
             "keyc": {"keyca": "valca"},
         }

    def test_non_existing_path(self):
        config_paths = test_dir / "config1-absent.yaml"
        result = load_and_merge_configs([config_paths])
        assert isinstance(result, Failure)
        err_msg = result.failure().get("error", "")
        assert "File not found" in err_msg

    def test_unsupported_format_file(self):
        config_paths = test_dir / "config1.xml"
        result = load_and_merge_configs([config_paths])
        assert isinstance(result, Failure)
        err_msg = result.failure().get("error", "")
        assert "Unsupported file type: .xml" in err_msg
