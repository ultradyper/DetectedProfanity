"""CLI tests: cli.py и python -m detected_profanity."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PY = PROJECT_ROOT / "cli.py"
PYTHON = sys.executable

ENV = {**__import__("os").environ, "NO_COLOR": "1", "TERM": "dumb", "PYTHONIOENCODING": "utf-8"}


def run_cli(*args: str, input_text: str | None = None, timeout: float = 10) -> subprocess.CompletedProcess[str]:
    cmd = [PYTHON, str(CLI_PY), *args]
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=ENV,
        timeout=timeout,
    )


def run_module(*args: str, input_text: str | None = None, timeout: float = 10) -> subprocess.CompletedProcess[str]:
    cmd = [PYTHON, "-m", "detected_profanity", *args]
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=ENV,
        timeout=timeout,
    )


class TestCliPy:
    def test_cli_clean_russian_not_detected(self):
        result = run_cli("привет")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip().lower() == "not detected"

    def test_cli_profane_russian_detected(self):
        result = run_cli("хуй")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip().lower() == "detected"

    def test_cli_profane_in_sentence(self):
        result = run_cli("пошёл на хуй")
        assert result.returncode == 0
        assert result.stdout.strip().lower() == "detected"

    def test_cli_clean_sentence_not_detected(self):
        result = run_cli("привет, как дела?")
        assert result.returncode == 0
        assert result.stdout.strip().lower() == "not detected"

    def test_cli_allowlist_not_detected(self):
        for word in ["мандарин", "assassin", "художник"]:
            result = run_cli(word)
            assert result.stdout.strip().lower() == "not detected", f"allowlist failed for {word}: {result.stdout}"

    def test_cli_help_long(self):
        result = run_cli("--help")
        assert result.returncode == 0
        out = result.stdout.lower()
        assert "использование" in out or "usage" in out
        assert "detectedprofanity" in out or "repl" in out

    def test_cli_help_short_flag(self):
        result = run_cli("-h")
        assert result.returncode == 0
        assert "repl" in result.stdout.lower() or "использование" in result.stdout.lower()

    def test_cli_stdin_pipe_clean(self):
        result = run_cli(input_text="привет\n")
        assert result.returncode == 0
        assert result.stdout.strip().lower() == "not detected"

    def test_cli_stdin_pipe_profane(self):
        result = run_cli(input_text="хуй\n")
        assert result.returncode == 0
        assert result.stdout.strip().lower() == "detected"


class TestModuleCli:
    def test_module_profane_english_yes(self):
        result = run_module("fuck")
        assert result.returncode == 1, result.stdout + result.stderr
        assert "YES" in result.stdout
        assert "profanity: YES" in result.stdout

    def test_module_clean_no(self):
        result = run_module("привет")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "profanity: NO" in result.stdout

    def test_module_help(self):
        result = run_module("--help")
        assert result.returncode == 0
        out = result.stdout.lower() + result.stderr.lower()
        assert "usage" in out
        assert "detected_profanity" in out or "detected" in out
        assert "--censor" in out
        assert "--json" in out

    def test_module_help_short(self):
        result = run_module("-h")
        assert result.returncode == 0
        assert "usage" in (result.stdout + result.stderr).lower()

    def test_module_censor_mode(self):
        result = run_module("--censor", "охуеть это тест")
        assert result.returncode == 1
        assert "охуеть" not in result.stdout
        assert "*" in result.stdout
        assert "это тест" in result.stdout

    def test_module_censor_custom_repl(self):
        result = run_module("--censor", "--repl", "#", "хуй тест")
        assert result.returncode == 1
        assert "хуй" not in result.stdout
        assert "#" in result.stdout
        assert "тест" in result.stdout

    def test_module_censor_clean_text(self):
        result = run_module("--censor", "привет мир")
        assert result.returncode == 0
        assert "привет мир" in result.stdout

    def test_module_json_with_profanity(self):
        result = run_module("--json", "хуй")
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["has_profanity"] is True
        assert payload["text"] == "хуй"
        assert isinstance(payload["matches"], list)
        assert len(payload["matches"]) >= 1

    def test_module_json_without_profanity(self):
        result = run_module("--json", "привет мир")
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["has_profanity"] is False
        assert payload["matches"] == []

    def test_module_json_with_censor(self):
        result = run_module("--json", "--censor", "блядь")
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["has_profanity"] is True
        assert "censored" in payload
        assert "*" in payload["censored"]
        assert "блядь" not in payload["censored"]

    def test_module_stdin_pipe(self):
        result = run_module(input_text="хуй\n")
        assert result.returncode == 1
        assert "YES" in result.stdout

    def test_module_stdin_pipe_clean(self):
        result = run_module(input_text="привет\n")
        assert result.returncode == 0
        assert "NO" in result.stdout

    def test_module_exit_codes(self):
        clean = run_module("привет")
        profane = run_module("хуй")
        empty = run_module(input_text="\n")
        assert clean.returncode == 0
        assert profane.returncode == 1
        assert empty.returncode == 2
        assert "empty input" in empty.stderr.lower()

    def test_module_lang_filter(self):
        ru_fuck = run_module("--lang", "ru", "fuck")
        assert ru_fuck.returncode == 0
        assert "NO" in ru_fuck.stdout

        en_huy = run_module("--lang", "en", "хуй")
        assert en_huy.returncode == 0
        assert "NO" in en_huy.stdout

        ru_huy = run_module("--lang", "ru", "хуй")
        assert ru_huy.returncode == 1
        assert "YES" in ru_huy.stdout

        en_fuck = run_module("--lang", "en", "fuck")
        assert en_fuck.returncode == 1
        assert "YES" in en_fuck.stdout

    def test_module_version(self):
        result = run_module("--version")
        assert result.returncode == 0
        out = result.stdout + result.stderr
        assert "1.0.0" in out or "version" in out.lower()
