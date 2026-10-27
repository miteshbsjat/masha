import logging
from pathlib import Path

import pytest

from masha.exceptions import PluginLoadError, TemplateRenderError
from masha.template_renderer import (
    load_functions_from_directory,
    load_functions_from_file,
    render_template_file,
    render_templates_with_filters,
)

pkg_dir = Path(__file__).parent.parent / "masha"
filters_path = pkg_dir / "filters"


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


class TestConfigRenderingBehaviour:
    def test_nested_dicts_rendered(self):
        rendered = render_templates_with_filters(
            {"a": "x", "n": {"m": {"k": "{{ a }}-deep"}}}
        )
        assert rendered["n"]["m"]["k"] == "x-deep"

    def test_chained_references_resolve(self):
        inp = {"d": "{{ c }}!", "c": "{{ b }}", "b": "{{ a }}", "a": "end"}
        assert render_templates_with_filters(inp)["d"] == "end!"

    def test_non_string_values_preserved(self):
        inp = {"i": 1, "f": 1.5, "b": True, "n": None, "l": [1, 2]}
        assert render_templates_with_filters(inp) == inp

    def test_non_convergence_warns(self, caplog):
        # Each pass appends another "x", so it never stabilises.
        with caplog.at_level(logging.WARNING, logger="masha"):
            rendered = render_templates_with_filters(
                {"a": "x{{ a }}"}, max_iterations=3
            )
        assert "did not converge after 3 iterations" in caplog.text
        assert rendered["a"].startswith("xxx")

    def test_converged_rendering_does_not_warn(self, caplog):
        with caplog.at_level(logging.WARNING, logger="masha"):
            render_templates_with_filters({"a": "1", "b": "{{ a }}"})
        assert caplog.records == []

    def test_unknown_filter_raises(self):
        with pytest.raises(TemplateRenderError, match="no_such_filter"):
            render_templates_with_filters({"a": "{{ 'x' | no_such_filter }}"})

    def test_custom_tests_directory(self, tmp_path):
        (tmp_path / "t.py").write_text(
            "def big(n):\n    return n > 10\n", encoding="utf-8"
        )
        rendered = render_templates_with_filters(
            {"n": 11, "s": "{{ 'yes' if n is big else 'no' }}"},
            tests_directory=tmp_path,
        )
        assert rendered["s"] == "yes"

    def test_safe_method_calls_still_allowed(self):
        rendered = render_templates_with_filters(
            {"a": "hello", "b": "{{ a.upper() }}-{{ a.split('l') | length }}"}
        )
        assert rendered["b"] == "HELLO-3"


class TestLoadFunctionsEdgeCases:
    def test_non_python_file_returns_empty(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("def f(): pass\n", encoding="utf-8")
        assert load_functions_from_file(path) == {}

    def test_subdirectory_named_like_py_file_skipped(self, tmp_path):
        (tmp_path / "pkg.py").mkdir()
        (tmp_path / "f.py").write_text(
            "def ok(s):\n    return s\n", encoding="utf-8"
        )
        assert set(load_functions_from_directory(tmp_path)) == {"ok"}

    def test_later_file_wins_on_name_clash(self, tmp_path):
        (tmp_path / "a.py").write_text(
            "def f(s):\n    return 'a'\n", encoding="utf-8"
        )
        (tmp_path / "b.py").write_text(
            "def f(s):\n    return 'b'\n", encoding="utf-8"
        )
        assert load_functions_from_directory(tmp_path)["f"]("") == "b"

    def test_classes_and_lambdas_assigned_names(self, tmp_path):
        (tmp_path / "f.py").write_text(
            "class Upper:\n    pass\n"
            "shout = lambda s: s.upper()\n"
            "def real(s):\n    return s\n",
            encoding="utf-8",
        )
        # Classes are not functions; module-level lambdas are.
        assert set(load_functions_from_directory(tmp_path)) == {
            "real",
            "shout",
        }

    def test_empty_directory(self, tmp_path):
        assert load_functions_from_directory(tmp_path) == {}

    def test_path_is_file_not_directory(self, tmp_path):
        path = tmp_path / "f.py"
        path.write_text("", encoding="utf-8")
        with pytest.raises(PluginLoadError, match="Not a directory"):
            load_functions_from_directory(path)


class TestRenderTemplateFileEdgeCases:
    def test_uses_filters_and_tests(self, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text(
            "{{ name | uppercase }} {{ 'even' if n is is_even else 'odd' }}",
            encoding="utf-8",
        )
        output = tmp_path / "out.txt"
        render_template_file(
            template,
            output,
            {"name": "masha", "n": 4},
            filters_directory=pkg_dir / "filters",
            tests_directory=pkg_dir / "tests",
        )
        assert output.read_text(encoding="utf-8") == "MASHA even"

    def test_include_from_template_directory(self, tmp_path):
        (tmp_path / "part.j2").write_text("part:{{ x }}", encoding="utf-8")
        template = tmp_path / "main.j2"
        template.write_text("{% include 'part.j2' %}", encoding="utf-8")
        output = tmp_path / "out.txt"
        render_template_file(template, output, {"x": 1})
        assert output.read_text(encoding="utf-8") == "part:1"

    def test_sandbox_applies_to_template_files(self, tmp_path):
        template = tmp_path / "evil.j2"
        template.write_text("{{ ''.__class__ }}", encoding="utf-8")
        output = tmp_path / "out.txt"
        with pytest.raises(TemplateRenderError, match="unsafe"):
            render_template_file(template, output, {})
        assert not output.exists()

    def test_overwrites_existing_output(self, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text("new", encoding="utf-8")
        output = tmp_path / "out.txt"
        output.write_text("old content that is longer", encoding="utf-8")
        render_template_file(template, output, {})
        assert output.read_text(encoding="utf-8") == "new"

    def test_unicode_round_trip(self, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text("नमस्ते {{ who }}", encoding="utf-8")
        output = tmp_path / "out.txt"
        render_template_file(template, output, {"who": "Маша"})
        assert output.read_text(encoding="utf-8") == "नमस्ते Маша"

    def test_unwritable_output_raises(self, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text("x", encoding="utf-8")
        output_dir = tmp_path / "out_is_a_dir"
        output_dir.mkdir()
        with pytest.raises(TemplateRenderError, match="Cannot write output"):
            render_template_file(template, output_dir, {})

    def test_missing_template_raises(self, tmp_path):
        with pytest.raises(TemplateRenderError):
            render_template_file(
                tmp_path / "absent.j2", tmp_path / "out.txt", {}
            )
