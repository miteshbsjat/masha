from pathlib import Path

import pytest

from masha.config_loader import load_and_merge_configs
from masha.config_validator import load_model_class, validate_config
from masha.env_loader import resolve_env_variables
from masha.exceptions import ModelValidationError
from masha.template_renderer import render_templates_with_filters

test_dir = Path(__file__).parent
model_file = test_dir / "model.py"


class TestConfigValidator:
    def test_full_pipeline(self, monkeypatch):
        monkeypatch.delenv("MASHA_DEBUG", raising=False)
        merged_config = load_and_merge_configs(
            [test_dir / "config-a.yaml", test_dir / "config-b.yaml"]
        )
        model_class = load_model_class(model_file, "ConfigModel")

        env_config = resolve_env_variables(merged_config)
        filters_path = test_dir.parent / "masha" / "filters"
        temp_config = render_templates_with_filters(env_config, filters_path)

        assert temp_config == {
            "name": "MITESH",
            "version": "0.0.1",
            "debug": "false",
            "x": "Mitesh",
            "age": 14,
            "f": "Mitesh",
            "c": {"d": "Mitesh", "e": "Mitesh"},
        }
        instance = validate_config(temp_config, model_class)
        assert instance.age == 14

    def test_invalid_config_raises(self):
        model_class = load_model_class(model_file, "ConfigModel")
        config = {"name": "a", "version": "1", "debug": False, "age": 200}
        with pytest.raises(ModelValidationError, match="invalid"):
            validate_config(config, model_class)

    def test_missing_class_raises(self):
        with pytest.raises(ModelValidationError, match="not found"):
            load_model_class(model_file, "NoSuchModel")

    def test_non_model_class_raises(self):
        with pytest.raises(ModelValidationError, match="not a subclass"):
            load_model_class(model_file, "field_validator")

    def test_broken_model_file_raises(self, tmp_path):
        bad = tmp_path / "bad_model.py"
        bad.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        with pytest.raises(ModelValidationError, match="boom"):
            load_model_class(bad, "Anything")
