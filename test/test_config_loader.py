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

    @pytest.mark.parametrize("name", ["c.yml", "c.YAML", "c.Yaml"])
    def test_yaml_suffix_variants(self, tmp_path, name):
        path = tmp_path / name
        path.write_text("a: 1\n", encoding="utf-8")
        assert load_config(path) == {"a": 1}

    def test_malformed_toml(self, tmp_path):
        path = tmp_path / "bad.toml"
        path.write_text("a = \n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="Cannot parse"):
            load_config(path)

    def test_properties_without_section_header(self, tmp_path):
        path = tmp_path / "bad.properties"
        path.write_text("key = value\n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="Cannot parse"):
            load_config(path)

    def test_missing_properties_file(self, tmp_path):
        # configparser.read() silently ignores missing files; we must not.
        with pytest.raises(ConfigLoadError, match="File not found"):
            load_config(tmp_path / "absent.properties")

    def test_non_utf8_file(self, tmp_path):
        path = tmp_path / "latin1.json"
        path.write_bytes(b'{"a": "\xff"}')
        with pytest.raises(ConfigLoadError, match="Cannot read"):
            load_config(path)

    def test_directory_with_config_suffix(self, tmp_path):
        path = tmp_path / "dir.yaml"
        path.mkdir()
        with pytest.raises(ConfigLoadError, match="Cannot read"):
            load_config(path)

    @pytest.mark.parametrize(
        ("name", "content"),
        [("s.yaml", "just a string\n"), ("n.json", "42"), ("l.json", "[1]")],
    )
    def test_scalar_or_list_top_level_rejected(self, tmp_path, name, content):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="must be a mapping"):
            load_config(path)

    def test_error_chains_original_exception(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{", encoding="utf-8")
        with pytest.raises(ConfigLoadError) as info:
            load_config(path)
        assert info.value.__cause__ is not None


class TestMergePrecedence:
    def test_later_files_win(self, tmp_path):
        paths = []
        for i, content in enumerate(
            ["a: 1\nb: 1\n", "b: 2\nc: 2\n", "c: 3\n"]
        ):
            path = tmp_path / f"c{i}.yaml"
            path.write_text(content, encoding="utf-8")
            paths.append(path)
        assert load_and_merge_configs(paths) == {"a": 1, "b": 2, "c": 3}

    def test_mixed_formats_and_str_paths(self, tmp_path):
        (tmp_path / "a.toml").write_text('x = "toml"\n', encoding="utf-8")
        (tmp_path / "b.json").write_text('{"y": "json"}', encoding="utf-8")
        result = load_and_merge_configs(
            [str(tmp_path / "a.toml"), str(tmp_path / "b.json")]
        )
        assert result == {"x": "toml", "y": "json"}

    def test_stops_at_first_bad_file(self, tmp_path):
        good = tmp_path / "good.yaml"
        good.write_text("a: 1\n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="absent.yaml"):
            load_and_merge_configs([good, tmp_path / "absent.yaml", good])
