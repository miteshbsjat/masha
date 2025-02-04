import unittest
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from returns.result import Result, Success, Failure

# directory reach
directory = Path(__file__).parent.parent / "masha"
# setting path
sys.path.append(str(directory))
from config_loader import merge_configs, load_and_merge_configs


class TestMergeConfigs(unittest.TestCase):
    def test_empty_configs(self):
        result = merge_configs({})
        self.assertEqual(result, {})

    def test_single_config(self):
        config1 = {'a': 1, 'b': 2}
        config2 = {'a': 3}
        expected = {'a': 3, 'b': 2}
        result = merge_configs([config1, config2])
        self.assertEqual(result, expected)

    def test_multiple_configs_no_overlap(self):
        config1 = {'a': 1, 'b': 2}
        config2 = {'c': 3, 'd': 4}
        result = merge_configs([config1, config2])
        self.assertEqual(result, {'a': 1, 'b': 2, 'c': 3, 'd': 4})

    def test_multiple_configs_with_overlap(self):
        config1 = {'a': 1, 'b': 2}
        config2 = {'b': 3, 'c': 4}
        result = merge_configs([config1, config2])
        self.assertEqual(result, {'a': 1, 'b': 3, 'c': 4})

    def test_nested_configs(self):
        config1 = {'a': {'x': 1}, 'b': 2}
        config2 = {'a': {'y': 2}, 'c': 3}
        result = merge_configs([config1, config2])
        self.assertEqual(result, {'a': {'y': 2}, 'b': 2, 'c': 3})

##########################
test_dir = str(Path(__file__).parent)

class TestLoadAndMergeConfigs(unittest.TestCase):

    def test_happy_path(self):
        # Arrange
        config_paths = Path(test_dir) / "config1.yaml"
        
        # Act
        result = load_and_merge_configs([config_paths])
        config = None
        match result:
            case Success(value):
                config = value
        
        # Assert
        self.assertNotEqual(config, None)
        self.assertEqual(config, {'keya': 'vala', 'keyb': 'val2', 'keyc': {'keyca': 'valca'}})

    def test_happy_multiple_paths(self):
        # Arrange
        config_path1 = Path(test_dir) / "config1.yaml"
        config_path2 = Path(test_dir) / "config2.json"
        
        # Act
        result = load_and_merge_configs([config_path1, config_path2])
        config = None
        match result:
            case Success(value):
                config = value
        
        # Assert
        self.assertNotEqual(config, None)
        self.assertEqual(config, {'keya': 'vala', 'keyb': 'valb_json', 'keyc': {'keyca': 'valca'}})

    def test_non_existing_path(self):
        # Arrange
        config_paths = Path(test_dir) / "config1-absent.yaml"
        
        # Act
        result = load_and_merge_configs([config_paths])
        config = None
        match result:
            case Success(value):
                config = value
            case Failure(value):
                config = value
        
        # Assert
        self.assertNotEqual(config, None)
        err_msg = config.get("error", None)
        self.assertNotEqual(err_msg, None)
        self.assertGreaterEqual(err_msg.find("File not found"), 0)

    def test_unsupported_format_file(self):
        # Arrange
        config_paths = Path(test_dir) / "config1.xml"
        
        # Act
        result = load_and_merge_configs([config_paths])
        config = None
        match result:
            case Success(value):
                config = value
            case Failure(value):
                config = value
        
        # Assert
        self.assertNotEqual(config, None)
        err_msg = config.get("error", None)
        self.assertNotEqual(err_msg, None)
        self.assertGreaterEqual(err_msg.find("Unsupported file type: .xml"), 0)


if __name__ == '__main__':
    unittest.main()