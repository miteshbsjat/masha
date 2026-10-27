from pathlib import Path

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
