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


##########################
# test_dir = str(Path(__file__).parent)

class TestTemplateRenderer(unittest.TestCase):

    def test_happy_path(self):
        inp = {"c": "from {{ b }}", "a": "val_a", "b": "from_{{ a | uppercase }}", "z": 4}
        # inp = {"name": "test", "version": "0.0.2", "debug": "false", "age": 14}
        filters_path = Path(__file__).parent.parent / "masha" / "filters"
        rendered = render_templates_with_filters(inp, str(filters_path))
        # Arrange
        expected_dict = {'a': 'val_a', 'b': 'from_VAL_A', 'c': 'from from_VAL_A', 'z': 4}
        
        # Assert
        self.assertNotEqual(rendered, None)
        self.assertEqual(rendered, expected_dict)


if __name__ == '__main__':
    unittest.main()