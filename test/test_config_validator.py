from pathlib import Path
from types import MappingProxyType

import pytest
from pydantic import ValidationError

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

    def test_returns_model_instance(self):
        model_class = load_model_class(model_file, "ConfigModel")
        config = {"name": "a", "version": "1", "debug": "true", "age": 3}
        instance = validate_config(config, model_class)
        assert isinstance(instance, model_class)
        assert instance.debug is True  # pydantic coercion applied

    def test_accepts_read_only_mapping(self):
        model_class = load_model_class(model_file, "ConfigModel")
        config = MappingProxyType(
            {"name": "a", "version": "1", "debug": False, "age": 3}
        )
        assert validate_config(config, model_class).age == 3

    def test_missing_field_reported(self):
        model_class = load_model_class(model_file, "ConfigModel")
        with pytest.raises(ModelValidationError, match="age") as info:
            validate_config(
                {"name": "a", "version": "1", "debug": False}, model_class
            )
        assert isinstance(info.value.__cause__, ValidationError)

    def test_non_python_model_file_raises(self, tmp_path):
        path = tmp_path / "model.txt"
        path.write_text("class X: pass\n", encoding="utf-8")
        with pytest.raises(ModelValidationError, match="Cannot load model"):
            load_model_class(path, "X")

    def test_plain_class_rejected(self, tmp_path):
        path = tmp_path / "plain.py"
        path.write_text("class Plain:\n    pass\n", encoding="utf-8")
        with pytest.raises(ModelValidationError, match="not a subclass"):
            load_model_class(path, "Plain")

    def test_model_with_forward_reference(self, tmp_path):
        path = tmp_path / "fwd.py"
        path.write_text(
            "from __future__ import annotations\n"
            "from pydantic import BaseModel\n"
            "class Child(BaseModel):\n    v: int\n"
            "class Parent(BaseModel):\n    child: Child\n",
            encoding="utf-8",
        )
        parent = load_model_class(path, "Parent")
        assert validate_config({"child": {"v": 1}}, parent).child.v == 1
