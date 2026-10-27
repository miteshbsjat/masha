import logging
from pathlib import Path

import pytest
import yaml

from masha.config_loader import load_and_merge_configs
from masha.env_loader import resolve_env_variables

test_dir = Path(__file__).parent


class TestEnvLoader:
    def test_happy_path(self, monkeypatch):
        config_path = test_dir / "env_config.yaml"
        with open(config_path, encoding="utf-8") as f:
            expected_dict = yaml.safe_load(f)

        config = load_and_merge_configs([config_path])
        assert config == expected_dict

        monkeypatch.setenv("ENV_B", "default_not_used_b")
        monkeypatch.delenv("ENV_C", raising=False)
        monkeypatch.delenv("ENV_D", raising=False)
        env_config = resolve_env_variables(config)
        assert env_config["a"] == {
            "b": "default_not_used_b",
            "c": "default_used_c",
            "d": None,
        }

    def test_input_not_mutated(self, monkeypatch):
        monkeypatch.setenv("ENV_X", "x")
        config = {"a": {"b": "${ENV_X:y}"}}
        resolve_env_variables(config)
        assert config == {"a": {"b": "${ENV_X:y}"}}

    def test_lists_resolved(self, monkeypatch):
        monkeypatch.setenv("ENV_X", "x")
        assert resolve_env_variables({"a": ["${ENV_X:y}", 1]}) == {
            "a": ["x", 1]
        }

    def test_whitespace_after_colon_is_ignored(self, monkeypatch):
        monkeypatch.delenv("ENV_X", raising=False)
        assert resolve_env_variables({"a": "${ENV_X:   dflt}"}) == {
            "a": "dflt"
        }

    def test_empty_default(self, monkeypatch):
        monkeypatch.delenv("ENV_X", raising=False)
        assert resolve_env_variables({"a": "${ENV_X:}"}) == {"a": ""}

    def test_empty_env_value_wins_over_default(self, monkeypatch):
        monkeypatch.setenv("ENV_X", "")
        assert resolve_env_variables({"a": "${ENV_X:dflt}"}) == {"a": ""}

    def test_null_default_only_when_unset(self, monkeypatch):
        monkeypatch.setenv("ENV_X", "null")
        assert resolve_env_variables({"a": "${ENV_X:null}"}) == {"a": "null"}

    @pytest.mark.parametrize(
        "value",
        ["prefix ${ENV_X:y}", "${ENV_X:y} suffix", "$ENV_X", "${ENV_X}"],
    )
    def test_only_whole_value_placeholders_resolved(self, monkeypatch, value):
        monkeypatch.setenv("ENV_X", "x")
        assert resolve_env_variables({"a": value}) == {"a": value}

    def test_deeply_nested(self, monkeypatch):
        monkeypatch.setenv("ENV_X", "x")
        config = {"a": [{"b": ["${ENV_X:y}"]}], "n": 1, "f": None}
        assert resolve_env_variables(config) == {
            "a": [{"b": ["x"]}],
            "n": 1,
            "f": None,
        }

    @pytest.mark.parametrize("value", [None, 1, 1.5, True])
    def test_non_container_top_level_passthrough(self, value):
        assert resolve_env_variables(value) == value

    def test_env_value_not_logged(self, monkeypatch, caplog):
        monkeypatch.setenv("ENV_SECRET", "hunter2")
        with caplog.at_level(logging.DEBUG, logger="masha"):
            resolve_env_variables({"pw": "${ENV_SECRET:x}"})
        assert "ENV_SECRET" in caplog.text
        assert "hunter2" not in caplog.text
