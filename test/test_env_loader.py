import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from returns.result import Result, Success, Failure
import yaml

# directory reach
directory = Path(__file__).parent.parent / "masha"
# setting path
sys.path.append(str(directory))
from config_loader import merge_configs, load_and_merge_configs
from env_loader import resolve_env_variables


##########################
test_dir = str(Path(__file__).parent)

class TestEnvLoader(unittest.TestCase):

    def test_happy_path(self):
        # Arrange
        config_paths = Path(test_dir) / "env_config.yaml"
        with open(str(config_paths), "r") as f:
            expected_dict = yaml.safe_load(f)
        
        # Act
        result = load_and_merge_configs([config_paths])
        config = None
        match result:
            case Success(value):
                config = value
        
        # Assert
        self.assertNotEqual(config, None)
        self.assertEqual(config, expected_dict)

        # Replace env vars
        os.environ["ENV_B"] = "default_not_used_b"
        env_config = resolve_env_variables(config)
        self.assertEqual(env_config['a']['b'], os.environ["ENV_B"])


if __name__ == '__main__':
    unittest.main()