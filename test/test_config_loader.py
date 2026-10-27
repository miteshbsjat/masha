from pathlib import Path

import pytest

from masha.config_loader import (
    load_and_merge_configs,
    load_config,
    merge_configs,
)
from masha.exceptions import ConfigLoadError

test_dir = Path(__file__).parent


class TestMergeConfigs:
    def test_empty_configs(self):
        assert merge_configs([]) == {}

    def test_single_config(self):
        config1 = {"a": 1, "b": 2}
        config2 = {"a": 3}
        assert merge_configs([config1, config2]) == {"a": 3, "b": 2}

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

    def test_inputs_not_mutated(self):
        config1 = {"a": 1}
        config2 = {"a": 2}
        merge_configs([config1, config2])
        assert config1 == {"a": 1}

    def test_none_skipped(self):
        assert merge_configs([None, {"a": 1}]) == {"a": 1}


class TestLoadAndMergeConfigs:
    def test_empty_file_skipped(self):
        assert load_and_merge_configs([test_dir / "config-d.yaml"]) == {}

    def test_happy_path(self):
        assert load_and_merge_configs([test_dir / "config1.yaml"]) == {
            "keya": "vala",
            "keyb": "val2",
            "keyc": {"keyca": "valca"},
        }

    def test_happy_multiple_paths(self):
        result = load_and_merge_configs(
            [test_dir / "config1.yaml", test_dir / "config2.json"]
        )
        assert result == {
            "keya": "vala",
            "keyb": "valb_json",
            "keyc": {"keyca": "valca"},
        }

    def test_non_existing_path(self):
        with pytest.raises(ConfigLoadError, match="File not found"):
            load_and_merge_configs([test_dir / "config1-absent.yaml"])

    def test_unsupported_format_file(self):
        with pytest.raises(
            ConfigLoadError, match="Unsupported file type: .xml"
        ):
            load_and_merge_configs([test_dir / "config1.xml"])


class TestLoadConfig:
    def test_toml(self, tmp_path):
        path = tmp_path / "c.toml"
        path.write_text('a = 1\n[b]\nc = "d"\n', encoding="utf-8")
        assert load_config(path) == {"a": 1, "b": {"c": "d"}}

    def test_properties_no_interpolation(self, tmp_path):
        path = tmp_path / "c.properties"
        path.write_text("[db]\nurl = x%(y)s\n", encoding="utf-8")
        assert load_config(path) == {"db": {"url": "x%(y)s"}}

    def test_malformed_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="Cannot parse"):
            load_config(path)

    def test_malformed_yaml(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("a: [1, 2\n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="Cannot parse"):
            load_config(path)

    def test_yaml_python_tags_rejected(self, tmp_path):
        path = tmp_path / "evil.yaml"
        path.write_text(
            "a: !!python/object/apply:os.system ['echo pwned']\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigLoadError, match="Cannot parse"):
            load_config(path)

    def test_top_level_must_be_mapping(self, tmp_path):
        path = tmp_path / "list.yaml"
        path.write_text("- 1\n- 2\n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="must be a mapping"):
            load_config(path)
