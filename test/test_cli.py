from pathlib import Path

import pytest
from click.testing import CliRunner

from masha.cli import main

test_dir = Path(__file__).parent
pkg_dir = test_dir.parent / "masha"


@pytest.fixture
def runner():
    return CliRunner()


def _base_args(output: Path) -> list[str]:
    return [
        "-v", str(test_dir / "config-a.yaml"),
        "-v", str(test_dir / "config-b.yaml"),
        "-f", str(pkg_dir / "filters"),
        "-t", str(pkg_dir / "tests"),
        "-o", str(output),
    ]  # fmt: skip


class TestCli:
    def test_happy_path(self, runner, tmp_path, monkeypatch):
        monkeypatch.delenv("MASHA_DEBUG", raising=False)
        output = tmp_path / "out.txt"
        args = _base_args(output) + [
            "-m", str(test_dir / "model.py"),
            "-c", "ConfigModel",
            str(test_dir / "input.txt.j2"),
        ]  # fmt: skip
        result = runner.invoke(main, args)
        assert result.exit_code == 0, result.output
        text = output.read_text(encoding="utf-8")
        assert "My name is mitesh." in text
        assert "14 years even" in text

    def test_validation_failure_is_clean(self, runner, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("age: 999\n", encoding="utf-8")
        args = _base_args(tmp_path / "out.txt") + [
            "-v", str(bad),
            "-m", str(test_dir / "model.py"),
            "-c", "ConfigModel",
            str(test_dir / "input.txt.j2"),
        ]  # fmt: skip
        result = runner.invoke(main, args)
        assert result.exit_code == 1
        assert "Error:" in result.output
        assert "Traceback" not in result.output

    def test_model_without_class_is_usage_error(self, runner, tmp_path):
        args = _base_args(tmp_path / "out.txt") + [
            "-m", str(test_dir / "model.py"),
            str(test_dir / "input.txt.j2"),
        ]  # fmt: skip
        result = runner.invoke(main, args)
        assert result.exit_code == 2
        assert "must be given together" in result.output

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "masha" in result.output
