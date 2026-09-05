"""Independent behavioral requirements for developer checks and runtime smoke."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tomllib
from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

import pytest

from elbysodic import checks


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, Path("scripts") / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_required_checks_are_present_in_every_developer_gate() -> None:
    for full, quick in ((False, False), (True, False), (True, True)):
        commands = checks.check_commands(full=full, quick=quick)
        assert ["uv", "run", "ruff", "check", "."] in commands
        assert ["uv", "run", "ruff", "format", ".", "--check"] in commands
        assert ["uv", "run", "ty", "check", "src/elbysodic/", "tests/"] in commands
        assert ["uv", "run", "python", "scripts/kida_check.py"] in commands
        assert ["uv", "run", "milo", "verify", "src/elbysodic/cli.py"] in commands
        assert [
            "uv",
            "run",
            "--group",
            "docs",
            "--frozen",
            "python",
            "scripts/bengal_docs.py",
            "check",
        ] in commands
        assert ["node", "--test", "tests/client/composer.test.cjs"] in commands
        assert any("--baseline" in command for command in commands)
        assert any("warnings_as_errors=True" in arg for command in commands for arg in command)
    full_gate = checks.check_commands(full=True, base="test/base")
    assert ["uv", "run", "pytest", "-q", "--tb=short"] in full_gate
    assert full_gate[-1][-2:] == ["--base", "test/base"]


def test_canonical_gate_discovers_every_client_test_in_sorted_order(tmp_path, monkeypatch) -> None:
    client_root = tmp_path / "tests" / "client"
    client_root.mkdir(parents=True)
    (client_root / "z-last.test.cjs").write_text("")
    (client_root / "composer.test.cjs").write_text("")
    monkeypatch.setattr(checks, "REPO_ROOT", tmp_path)

    client_command = next(
        command for command in checks.check_commands() if command[:2] == ["node", "--test"]
    )

    assert client_command == [
        "node",
        "--test",
        "tests/client/composer.test.cjs",
        "tests/client/z-last.test.cjs",
    ]


@pytest.mark.parametrize(
    "failure",
    [
        "scripts/kida_check.py",
        "src/elbysodic/cli.py",
        "scripts/bengal_docs.py",
        "--baseline",
        "warnings_as_errors=True",
    ],
)
def test_gate_stops_on_template_contract_or_warning_failure(monkeypatch, failure: str) -> None:
    calls = []

    def run(command, *, check):
        calls.append(command)
        failed = any(failure in argument for argument in command)
        return subprocess.CompletedProcess(command, 7 if failed else 0)

    monkeypatch.setattr(checks.subprocess, "run", run)
    with pytest.raises(SystemExit) as exc:
        checks.run_commands(checks.check_commands(full=True))
    assert exc.value.code == 7
    assert any(failure in argument for argument in calls[-1])
    assert not any("pytest" in command for command in calls)


def test_missing_client_runtime_has_actionable_failure(monkeypatch, capsys) -> None:
    def missing(*args, **kwargs):
        raise FileNotFoundError("node")

    monkeypatch.setattr(checks.subprocess, "run", missing)
    with pytest.raises(SystemExit) as exc:
        checks.run_commands([["node", "--test", "tests/client/composer.test.cjs"]])
    assert exc.value.code == 127
    assert "'node' on PATH" in capsys.readouterr().err


def test_canonical_gate_can_route_output_to_a_host_owned_sink(monkeypatch) -> None:
    messages: list[str] = []

    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="check output")

    monkeypatch.setattr(checks.subprocess, "run", run)
    checks.run_commands([["example", "check"]], log=messages.append)

    assert messages == ["$ example check", "check output"]


def test_make_and_poe_share_the_canonical_gate() -> None:
    tasks = tomllib.loads(Path("pyproject.toml").read_text())["tool"]["poe"]["tasks"]
    assert tasks["check"]["cmd"] == "python -m elbysodic.checks"
    assert tasks["ci"]["cmd"] == "python -m elbysodic.checks --full"
    make = Path("Makefile").read_text()
    assert "check:\n\tuv run python -m elbysodic.checks\n" in make
    assert "ci:\n\tuv run python -m elbysodic.checks --full --base $(CONTRACT_DIFF_BASE)" in make


def test_shell_does_not_override_the_selected_python_runtime() -> None:
    make = shutil.which("make")
    assert make is not None
    result = subprocess.run(  # noqa: S603 -- fixed Make dry-run, resolved executable
        [make, "-n", "shell"], capture_output=True, text=True, check=True
    )
    assert "activate" in result.stdout
    assert "PYTHON_GIL=" not in result.stdout


def test_fragment_guidance_is_ignored_but_invalid_release_notes_fail(tmp_path, capsys) -> None:
    validator = _script("check_changelog_fragments")
    assert validator.main(["changelog.d/README.md", "changelog.d/AGENTS.md"]) == 0
    invalid = tmp_path / "+broken.fixed.md"
    invalid.write_text("- Wrong.\n\nSecond paragraph.")
    assert validator.main([str(invalid)]) == 1
    assert "should not start with a dash" in capsys.readouterr().err
    invalid.write_text("Writers can recover their draft after a failed submission.\n")
    assert validator.main([str(invalid)]) == 0


@pytest.mark.parametrize("gil", [True, False])
def test_probe_accepts_the_declared_supported_runtime(monkeypatch, gil: bool) -> None:
    smoke = _script("railway_probe_smoke")
    payload = {"runtime": {"build_id": "audit", "gil_enabled": gil}}
    monkeypatch.setattr(smoke, "_request", lambda *a, **k: (200, json.dumps(payload).encode(), []))
    smoke.verify_pounce_info("http://localhost", build_id="audit", expected_gil=gil)
    with pytest.raises(RuntimeError, match="expected gil_enabled"):
        smoke.verify_pounce_info("http://localhost", build_id="audit", expected_gil=not gil)


@pytest.mark.parametrize("gil", [None, "false", 0])
def test_probe_does_not_treat_missing_or_malformed_runtime_as_valid(monkeypatch, gil) -> None:
    smoke = _script("railway_probe_smoke")
    payload = {"runtime": {"build_id": "audit", "gil_enabled": gil}}
    monkeypatch.setattr(smoke, "_request", lambda *a, **k: (200, json.dumps(payload).encode(), []))
    with pytest.raises(TypeError, match="boolean gil_enabled"):
        smoke.verify_pounce_info("http://localhost", build_id="audit")


def test_probe_returns_http_error_status_body_and_headers(monkeypatch) -> None:
    smoke = _script("railway_probe_smoke")
    headers = Message()
    headers["Retry-After"] = "1"
    response = HTTPError(
        "http://localhost/readyz",
        503,
        "Service Unavailable",
        headers,
        BytesIO(b'{"status":"draining"}'),
    )

    def raise_http_error(*_args, **_kwargs):
        raise response

    monkeypatch.setattr(smoke, "urlopen", raise_http_error)

    assert smoke._request("http://localhost", "/readyz") == (
        503,
        b'{"status":"draining"}',
        [("Retry-After", "1")],
    )


def test_explicit_remote_runtime_check_requires_target_and_build_id() -> None:
    smoke = _script("railway_probe_smoke")
    with pytest.raises(SystemExit) as exc:
        smoke.main(["--expect-gil", "disabled"])
    assert exc.value.code == 2
