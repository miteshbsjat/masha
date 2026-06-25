import os
import sys
from pathlib import Path

import pytest
import yaml
from returns.result import Success

# directory reach
directory = Path(__file__).parent.parent / "masha"
sys.path.append(str(directory))
from config_loader import load_and_merge_configs
from env_loader import resolve_env_variables

test_dir = Path(__file__).parent


class TestEnvLoader:
    def test_happy_path(self):
        config_paths = test_dir / "env_config.yaml"
        with open(config_paths, "r") as f:
            expected_dict = yaml.safe_load(f)

        result = load_and_merge_configs([config_paths])
        assert isinstance(result, Success)
        assert result.unwrap() == expected_dict

        os.environ["ENV_B"] = "default_not_used_b"
        env_config = resolve_env_variables(result.unwrap())
        assert env_config["a"]["b"] == os.environ["ENV_B"]
