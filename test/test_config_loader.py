import unittest
import sys
from pathlib import Path
from typing import Dict, Any
# directory reach
directory = Path(__file__).parent.parent / "masha"
# setting path
sys.path.append(str(directory))
from config_loader import merge_configs


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

if __name__ == '__main__':
    unittest.main()