import sys
from pathlib import Path

import pytest
from returns.result import Failure, Success

# directory reach
directory = Path(__file__).parent.parent / "masha"
sys.path.append(str(directory))
from config_loader import load_and_merge_configs
from config_validator import load_model_class, validate_config
from env_loader import resolve_env_variables
from template_renderer import render_templates_with_filters
from logger_factory import create_logger

test_dir = Path(__file__).parent
logger = create_logger("masha")


class TestConfigValidator:
    def test_full_pipeline(self):
        config_a_path = test_dir / "config-a.yaml"
        config_b_path = test_dir / "config-b.yaml"

        result = load_and_merge_configs([config_a_path, config_b_path])
        assert isinstance(result, Success)
        merged_config = result.unwrap()
        assert merged_config is not None

        model_file = test_dir / "model.py"
        model_class = load_model_class(model_file, "ConfigModel")
        assert model_class is not None

        env_config = resolve_env_variables(merged_config)
        filters_path = Path(__file__).parent.parent / "masha" / "filters"
        temp_config = render_templates_with_filters(env_config, str(filters_path))

        expected_config = {
             "name": "MITESH",
             "version": "0.0.1",
             "debug": "false",
             "x": "Mitesh",
             "age": 14,
             "f": "Mitesh",
             "c": {"d": "Mitesh", "e": "Mitesh"},
         }
        assert temp_config == expected_config

        validation_result = validate_config(temp_config, model_class)
        assert isinstance(validation_result, Success)
