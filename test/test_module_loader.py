import importlib.util
import sys

import pytest

from masha.module_loader import import_module_from_path


class TestImportModuleFromPath:
    def test_imports_module(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("VALUE = 42\n", encoding="utf-8")
        module = import_module_from_path(path)
        assert module.VALUE == 42
        assert sys.modules[module.__name__] is module

    def test_same_stem_in_different_dirs_does_not_collide(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        (tmp_path / "a" / "mod.py").write_text("X = 'a'\n", encoding="utf-8")
        (tmp_path / "b" / "mod.py").write_text("X = 'b'\n", encoding="utf-8")
        mod_a = import_module_from_path(tmp_path / "a" / "mod.py")
        mod_b = import_module_from_path(tmp_path / "b" / "mod.py")
        assert mod_a.__name__ != mod_b.__name__
        assert (mod_a.X, mod_b.X) == ("a", "b")

    def test_module_name_is_not_importable_package_name(self, tmp_path):
        # A user file named like a stdlib module must not shadow it.
        path = tmp_path / "json.py"
        path.write_text("SHADOW = True\n", encoding="utf-8")
        module = import_module_from_path(path)
        assert module.__name__ != "json"
        import json

        assert not hasattr(json, "SHADOW")

    def test_non_python_file_rejected(self, tmp_path):
        path = tmp_path / "mod.txt"
        path.write_text("X = 1\n", encoding="utf-8")
        with pytest.raises(ImportError, match="Not a Python source file"):
            import_module_from_path(path)

    def test_missing_file_rejected(self, tmp_path):
        with pytest.raises(ImportError, match="Not a Python source file"):
            import_module_from_path(tmp_path / "absent.py")

    def test_directory_rejected(self, tmp_path):
        directory = tmp_path / "pkg.py"
        directory.mkdir()
        with pytest.raises(ImportError, match="Not a Python source file"):
            import_module_from_path(directory)

    def test_syntax_error_wrapped(self, tmp_path):
        path = tmp_path / "broken.py"
        path.write_text("def (:\n", encoding="utf-8")
        with pytest.raises(ImportError, match="Error while importing") as info:
            import_module_from_path(path)
        assert isinstance(info.value.__cause__, SyntaxError)

    def test_failed_module_removed_from_sys_modules(self, tmp_path):
        path = tmp_path / "boom.py"
        path.write_text("raise ValueError('boom')\n", encoding="utf-8")
        before = set(sys.modules)
        with pytest.raises(ImportError, match="boom") as info:
            import_module_from_path(path)
        assert isinstance(info.value.__cause__, ValueError)
        assert set(sys.modules) - before == set()

    def test_missing_spec_raises(self, tmp_path, monkeypatch):
        path = tmp_path / "mod.py"
        path.write_text("X = 1\n", encoding="utf-8")
        monkeypatch.setattr(
            importlib.util, "spec_from_file_location", lambda *a, **k: None
        )
        with pytest.raises(ImportError, match="Cannot create import spec"):
            import_module_from_path(path)
