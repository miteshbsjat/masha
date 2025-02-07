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
from template_renderer import render_templates_with_filters
from config_validator import load_model_class, validate_config
from logger_factory import create_logger

logger = create_logger("masha")


##########################
test_dir = str(Path(__file__).parent)

class TestConfigValidator(unittest.TestCase):

    def test_happy_path(self):
        # Arrange
        config_a_path = Path(test_dir) / "config-a.yaml"
        config_b_path = Path(test_dir) / "config-b.yaml"
        
        # Act
        result = load_and_merge_configs([config_a_path, config_b_path])
        config = None
        match result:
            case Success(value):
                config = value

        
        # Load the model class
        model_file = Path(test_dir) / "model.py"
        model_class = load_model_class(model_file, "ConfigModel")
        self.assertIsNotNone(model_class)

        # Load and merge all configuration files
        merged_config = None
        match load_and_merge_configs([config_a_path, config_b_path]):
            case Success(value):
                merged_config = value
            case Failure(value):
                logger.warning(f"Failed to load configs: {value}")
        self.assertIsNotNone(merged_config)

        logger.debug(merged_config)
        env_config = resolve_env_variables(merged_config)
        logger.debug(env_config)
        filters_path = Path(__file__).parent.parent / "masha" / "filters"
        logger.debug(filters_path)
        temp_config = render_templates_with_filters(
            env_config, str(filters_path)
        )
        logger.debug(temp_config)
        expected_config = {'name': 'MITESH', 'version': '0.0.1', 'debug': 'false', 'x': 'Mitesh', 'age': 14, 'f': 'Mitesh', 'c': {'d': 'Mitesh', 'e': 'Mitesh'}}
        self.assertEqual(temp_config, expected_config)

        # Validate the merged configuration
        # validate_merged_config(env_config, model_class)
        validation_result = validate_config(temp_config, model_class)
        self.assertIsInstance(validation_result, Success)
        if isinstance(validation_result, Success):
            logger.debug(f"Given config is valid {validation_result}")
        else:
            logger.warning(f"Given config is invalid {validation_result}")
        

if __name__ == '__main__':
    unittest.main()
