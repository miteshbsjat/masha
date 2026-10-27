from pathlib import Path

import pytest

from masha.exceptions import PluginLoadError, TemplateRenderError
from masha.template_renderer import (
    load_functions_from_directory,
    render_template_file,
    render_templates_with_filters,
)

filters_path = Path(__file__).parent.parent / "masha" / "filters"


class TestTemplateRenderer:
    def test_happy_path(self):
        inp = {
            "c": "from {{ b }}",
            "a": "val_a",
            "b": "from_{{ a | uppercase }}",
            "z": 4,
        }
        rendered = render_templates_with_filters(inp, filters_path)
        assert rendered == {
            "a": "val_a",
            "b": "from_VAL_A",
            "c": "from from_VAL_A",
            "z": 4,
        }
        assert inp["b"] == "from_{{ a | uppercase }}"

    def test_syntax_error_raises(self):
        with pytest.raises(TemplateRenderError):
            render_templates_with_filters({"a": "{{ unclosed"})

    @pytest.mark.parametrize(
        "payload",
        [
            "{{ ''.__class__.__mro__[1].__subclasses__() }}",
            "{{ cycler.__init__.__globals__.os }}",
            "{{ ''|attr('__class__') }}",
        ],
    )
    def test_sandbox_blocks_ssti(self, payload):
        with pytest.raises(TemplateRenderError):
            render_templates_with_filters({"a": payload})

    def test_missing_filters_directory_raises(self, tmp_path):
        with pytest.raises(PluginLoadError):
            render_templates_with_filters({"a": "b"}, tmp_path / "missing")


class TestLoadFunctions:
    def test_only_own_public_functions(self, tmp_path):
        (tmp_path / "f.py").write_text(
            "from os.path import join\n"
            "def shout(s):\n    return s.upper()\n"
            "def _hidden(s):\n    return s\n",
            encoding="utf-8",
        )
        (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
        assert set(load_functions_from_directory(tmp_path)) == {"shout"}

    def test_broken_filter_file_raises(self, tmp_path):
        (tmp_path / "bad.py").write_text("1/0\n", encoding="utf-8")
        with pytest.raises(PluginLoadError, match="division by zero"):
            load_functions_from_directory(tmp_path)


class TestRenderTemplateFile:
    def test_failed_render_does_not_create_output(self, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text("{{ x | no_such_filter }}", encoding="utf-8")
        output = tmp_path / "out.txt"
        with pytest.raises(TemplateRenderError):
            render_template_file(template, output, {"x": 1})
        assert not output.exists()

    def test_html_is_autoescaped(self, tmp_path):
        template = tmp_path / "page.html.j2"
        template.write_text("{{ x }}", encoding="utf-8")
        output = tmp_path / "page.html"
        render_template_file(template, output, {"x": "<b>"})
        assert output.read_text(encoding="utf-8") == "&lt;b&gt;"

    def test_text_is_not_escaped(self, tmp_path):
        template = tmp_path / "conf.yaml.j2"
        template.write_text("{{ x }}", encoding="utf-8")
        output = tmp_path / "conf.yaml"
        render_template_file(template, output, {"x": "<b>"})
        assert output.read_text(encoding="utf-8") == "<b>"
