import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from masha import __version__
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

    def test_without_model_skips_validation(self, runner, tmp_path):
        # age 999 would fail ConfigModel; without -m/-c it must still render.
        bad = tmp_path / "bad.yaml"
        bad.write_text("age: 999\n", encoding="utf-8")
        output = tmp_path / "out.txt"
        args = _base_args(output) + [
            "-v", str(bad), str(test_dir / "input.txt.j2"),
        ]  # fmt: skip
        result = runner.invoke(main, args)
        assert result.exit_code == 0, result.output
        assert "999 years odd" in output.read_text(encoding="utf-8")
        assert "Starting validation" not in result.stderr

    def test_class_without_model_is_usage_error(self, runner, tmp_path):
        args = _base_args(tmp_path / "out.txt") + [
            "-c", "ConfigModel", str(test_dir / "input.txt.j2"),
        ]  # fmt: skip
        result = runner.invoke(main, args)
        assert result.exit_code == 2

    def test_missing_input_file_is_usage_error(self, runner, tmp_path):
        args = _base_args(tmp_path / "out.txt") + [str(tmp_path / "nope.j2")]
        result = runner.invoke(main, args)
        assert result.exit_code == 2
        assert "does not exist" in result.output

    def test_variables_required(self, runner, tmp_path):
        result = runner.invoke(
            main, ["-o", str(tmp_path / "o"), str(test_dir / "input.txt.j2")]
        )
        assert result.exit_code == 2
        assert "--variables" in result.output

    def test_env_var_overrides_config(self, runner, tmp_path, monkeypatch):
        config = tmp_path / "c.yaml"
        config.write_text("who: ${MASHA_WHO:nobody}\n", encoding="utf-8")
        template = tmp_path / "t.j2"
        template.write_text("hi {{ who }}", encoding="utf-8")
        output = tmp_path / "out.txt"
        monkeypatch.setenv("MASHA_WHO", "masha")
        result = runner.invoke(
            main, ["-v", str(config), "-o", str(output), str(template)]
        )
        assert result.exit_code == 0, result.output
        assert output.read_text(encoding="utf-8") == "hi masha"

    def test_render_failure_leaves_no_output(self, runner, tmp_path):
        template = tmp_path / "t.j2"
        template.write_text("{{ x | missing_filter }}", encoding="utf-8")
        output = tmp_path / "out.txt"
        result = runner.invoke(
            main,
            ["-v", str(test_dir / "config1.yaml"), "-o", str(output),
             str(template)],
        )  # fmt: skip
        assert result.exit_code == 1
        assert "Error:" in result.stderr
        assert not output.exists()

    def test_verbose_shows_debug_logs_and_traceback(self, runner, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{", encoding="utf-8")
        result = runner.invoke(
            main,
            ["-V", "-v", str(bad), "-o", str(tmp_path / "o"),
             str(test_dir / "input.txt.j2")],
        )  # fmt: skip
        assert result.exit_code == 1
        assert "| DEBUG |" in result.stderr
        assert "Traceback" in result.stderr

    def test_non_verbose_hides_debug_logs(self, runner, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{", encoding="utf-8")
        result = runner.invoke(
            main,
            ["-v", str(bad), "-o", str(tmp_path / "o"),
             str(test_dir / "input.txt.j2")],
        )  # fmt: skip
        assert result.exit_code == 1
        assert "| DEBUG |" not in result.stderr
        assert "Traceback" not in result.stderr

    def test_secret_values_never_logged(self, runner, tmp_path, monkeypatch):
        config = tmp_path / "c.yaml"
        config.write_text("password: ${MASHA_PW:x}\n", encoding="utf-8")
        template = tmp_path / "t.j2"
        template.write_text("ok", encoding="utf-8")
        monkeypatch.setenv("MASHA_PW", "s3cr3t-value")
        result = runner.invoke(
            main,
            ["-V", "-v", str(config), "-o", str(tmp_path / "o"),
             str(template)],
        )  # fmt: skip
        assert result.exit_code == 0, result.output
        assert "password" in result.stderr  # keys are logged...
        assert "s3cr3t-value" not in result.output  # ...values are not

    @pytest.mark.parametrize("verbose", [False, True])
    def test_unexpected_error_is_clean(
        self, runner, tmp_path, monkeypatch, verbose
    ):
        def explode(*args, **kwargs):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(
            "masha.cli.process_template_with_validation", explode
        )
        args = (["-V"] if verbose else []) + _base_args(tmp_path / "o")
        result = runner.invoke(main, args + [str(test_dir / "input.txt.j2")])
        assert result.exit_code == 1
        assert "fatal unexpected error" in result.stderr
        assert "CRITICAL" in result.stderr
        assert ("Traceback" in result.stderr) is verbose


def test_module_entry_point():
    # Runs the real `python -m masha.cli` entry point in a child process;
    # arguments are fixed, so there is no injection risk.
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "masha.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
        cwd=test_dir.parent,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout
