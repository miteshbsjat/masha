import sys
from pathlib import Path

# directory reach
directory = Path(__file__).parent.parent / "masha"
sys.path.append(str(directory))
from template_renderer import render_templates_with_filters


class TestTemplateRenderer:
    def test_happy_path(self):
        inp = {
             "c": "from {{ b }}",
             "a": "val_a",
             "b": "from_{{ a | uppercase }}",
             "z": 4,
        }
        filters_path = Path(__file__).parent.parent / "masha" / "filters"
        rendered = render_templates_with_filters(inp, str(filters_path))
        expected = {
             "a": "val_a",
             "b": "from_VAL_A",
             "c": "from from_VAL_A",
             "z": 4,
        }
        assert rendered == expected
