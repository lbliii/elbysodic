"""Local and staging probe smoke for Railway / Pounce deploy contracts."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_HOST = "127.0.0.1"
PROBE_PATHS = ("/health", "/livez", "/ready", "/readyz")


def _unused_port() -> int:
    with socket.socket() as sock:
        sock.bind((LOCAL_HOST, 0))
        return int(sock.getsockname()[1])


def _request(
    origin: str,
    path: str,
    *,
    method: str = "GET",
    timeout: float = 5.0,
) -> tuple[int, bytes, list[tuple[str, str]]]:
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Only absolute HTTP(S) origins are supported: {origin!r}")
    request = Request(f"{origin.rstrip('/')}{path}", method=method)  # noqa: S310 -- http/https only
    request.add_header("user-agent", "elbysodic-railway-probe-smoke/1")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 -- http/https only
            body = response.read()
            headers = list(response.headers.items())
            return int(response.status), body, headers
    except HTTPError as exc:
        body = exc.read()
        headers = list(exc.headers.items())
        return int(exc.code), body, headers


def _wait_for_status(
    origin: str,
    path: str,
    *,
    expected: int,
    timeout: float = 20.0,
) -> tuple[int, bytes]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, body, _ = _request(origin, path)
            if status == expected:
                return status, body
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            last_error = exc
        time.sleep(0.1)
    raise TimeoutError(f"{origin}{path} did not return {expected}") from last_error


def _start_local_server(port: int, db_path: Path) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("POUNCE_BUILD_ID", "railway-probe-smoke")
    env.setdefault("POUNCE_INTROSPECTION", "1")
    env["ELBYSODIC_RAILWAY_PROBE_SMOKE"] = "1"
    return subprocess.Popen(  # noqa: S603 -- fixed interpreter and argv
        [
            sys.executable,
            "-c",
            "from elbysodic.cli import main; main()",
            "serve",
            "--host",
            LOCAL_HOST,
            "--port",
            str(port),
            "--db-path",
            str(db_path),
            "--no-debug",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def verify_head_probes(origin: str) -> None:
    for path in PROBE_PATHS:
        status, _body, headers = _request(origin, path, method="HEAD")
        if status not in {200, 404}:
            raise RuntimeError(f"HEAD {path} returned HTTP {status}")
        if path in {"/health", "/livez", "/ready", "/readyz"} and status == 200:
            content_length = next(
                (value for name, value in headers if name.lower() == "content-length"),
                None,
            )
            if content_length is None:
                raise RuntimeError(f"HEAD {path} missing Content-Length")


def verify_readyz_ok(origin: str) -> None:
    status, body = _wait_for_status(origin, "/readyz", expected=200)
    payload = json.loads(body.decode("utf-8"))
    if payload.get("status") != "ok":
        raise RuntimeError(f"/readyz expected status ok, got {payload!r}")
    if status != 200:
        raise RuntimeError(f"/readyz returned HTTP {status}")


def verify_pounce_info(origin: str, *, build_id: str, expected_gil: bool | None = None) -> None:
    status, body, _ = _request(origin, "/_pounce/info")
    if status != 200:
        raise RuntimeError(f"/_pounce/info returned HTTP {status}")
    payload = json.loads(body.decode("utf-8"))
    runtime = payload.get("runtime", {})
    if runtime.get("build_id") != build_id:
        raise RuntimeError(
            f"/_pounce/info build_id expected {build_id!r}, got {runtime.get('build_id')!r}"
        )
    gil_enabled = runtime.get("gil_enabled")
    if not isinstance(gil_enabled, bool):
        raise TypeError("/_pounce/info did not report a boolean gil_enabled value")
    if expected_gil is not None and gil_enabled is not expected_gil:
        raise RuntimeError(f"/_pounce/info expected gil_enabled={expected_gil}, got {gil_enabled}")


def verify_readyz_draining_contract() -> None:
    from pounce._health import build_health_response
    from pounce._request_pipeline import maybe_build_builtin_response
    from pounce.config import ServerConfig

    status, _, body = build_health_response(worker_id=0, active_connections=0, draining=True)
    payload = json.loads(body.decode("utf-8"))
    if status != 503 or payload.get("status") != "draining":
        raise RuntimeError(f"expected draining health payload, got {status} {payload!r}")

    config = ServerConfig(health_check_path="/readyz")
    head = maybe_build_builtin_response(
        config,
        "HEAD",
        "/readyz",
        worker_id=0,
        active_connections=0,
        draining=True,
    )
    if head is None or head.status != 503:
        raise RuntimeError("HEAD /readyz should return 503 while draining")
    head_payload = json.loads(head.body.decode("utf-8"))
    if head_payload.get("status") != "draining":
        raise RuntimeError(f"HEAD /readyz draining payload unexpected: {head_payload!r}")


def run_local_smoke() -> int:
    port = _unused_port()
    db_path = REPO_ROOT / "var" / "railway-probe-smoke.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    process = _start_local_server(port, db_path)
    origin = f"http://{LOCAL_HOST}:{port}"
    build_id = os.environ.get("POUNCE_BUILD_ID", "railway-probe-smoke")
    try:
        _wait_for_status(origin, "/ready", expected=200)
        verify_head_probes(origin)
        verify_readyz_ok(origin)
        verify_pounce_info(origin, build_id=build_id, expected_gil=sys._is_gil_enabled())
        verify_readyz_draining_contract()
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=15)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        output = process.stdout.read() if process.stdout is not None else ""
        if process.returncode not in {0, -signal.SIGTERM, 128 + signal.SIGTERM} and output:
            print(output, file=sys.stderr)

    print(
        "Railway probe smoke passed: "
        f"HEAD probes ok, /readyz ok, /_pounce/info build_id={build_id!r}, "
        "and /readyz draining contract verified"
    )
    return 0


def run_remote_smoke(origin: str, *, build_id: str | None, expected_gil: bool | None = None) -> int:
    origin = origin.rstrip("/")
    verify_head_probes(origin)
    _wait_for_status(origin, "/ready", expected=200)
    verify_readyz_ok(origin)
    if build_id:
        verify_pounce_info(origin, build_id=build_id, expected_gil=expected_gil)
    print(f"Railway probe smoke passed against {origin}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--origin",
        help="Public staging/production origin. Omit to run the local subprocess smoke.",
    )
    parser.add_argument(
        "--build-id",
        help="Expected POUNCE_BUILD_ID value when checking /_pounce/info on a remote origin.",
    )
    parser.add_argument(
        "--expect-gil",
        choices=("enabled", "disabled"),
        help="Require a specific remote runtime posture (requires --origin and --build-id).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.expect_gil and not (args.origin and args.build_id):
        parser.error("--expect-gil requires --origin and --build-id")
    if args.origin:
        expected_gil = None if args.expect_gil is None else args.expect_gil == "enabled"
        return run_remote_smoke(args.origin, build_id=args.build_id, expected_gil=expected_gil)
    return run_local_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
