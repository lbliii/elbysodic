"""Prove an authenticated plotting-stream handoff on Railway staging.

The helper is deliberately pinned to the public staging host. It uses only
rendered login, wanted, plotting, and CSRF-protected form contracts; it never
prints credentials, cookies, account identifiers, message bodies, or tokens.
Run it before triggering a separate staging redeploy. It stays attached until
the retiring worker sends ``pounce.worker.draining``, reconnects, and verifies
one acknowledged write on each side of the handoff.
"""

from __future__ import annotations

import argparse
import http.client
import re
import ssl
import threading
import time
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

from elbysodic.services.auth import SEED_LOGIN_PHRASE, SESSION_COOKIE

STAGING_ORIGIN = "https://elbysodic-staging.up.railway.app"
COMMUNITY_PATH = "/c/x-men-apocalypse"
WANTED_PATH = f"{COMMUNITY_PATH}/wanted/human-un-liaison-for-b24"
APPLICANT_ACCOUNT = "writer@example.com"
OWNER_ACCOUNT = "charlie@example.com"
CSRF_RE = re.compile(r'name="_csrf_token" value="([^"]+)"')
FORM_RE = re.compile(r"<form\b.*?</form>", re.DOTALL)
PLOTTING_PATH_RE = re.compile(r'href="([^"]*/plotting/(\d+))"')


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    url: str
    text: str


class BrowserSession:
    def __init__(self, origin: str) -> None:
        self.origin = origin.rstrip("/")
        self.cookies = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def request(
        self,
        path: str,
        *,
        form: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> Response:
        data = urlencode(form).encode() if form is not None else None
        request = Request(  # noqa: S310 -- the origin is pinned to HTTPS staging
            urljoin(f"{self.origin}/", path.lstrip("/")),
            data=data,
            method="POST" if data is not None else "GET",
            headers={
                "User-Agent": "elbysodic-railway-drain-smoke/1",
                **(
                    {"Content-Type": "application/x-www-form-urlencoded"}
                    if data is not None
                    else {}
                ),
            },
        )
        try:
            with self.opener.open(request, timeout=timeout) as raw:
                body = raw.read().decode("utf-8", errors="replace")
                return Response(int(raw.status), raw.geturl(), body)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return Response(int(exc.code), exc.geturl(), body)

    def cookie_header(self) -> str:
        return "; ".join(f"{cookie.name}={cookie.value}" for cookie in self.cookies)


@dataclass(slots=True)
class StreamEvidence:
    ready_count: int = 0
    draining_count: int = 0
    message_markers: set[str] = field(default_factory=set)
    reconnect_failures: int = 0
    failure: str | None = None


class PlottingStreamMonitor:
    def __init__(self, origin: str, path: str, cookie_header: str) -> None:
        parsed = urlsplit(origin)
        if parsed.hostname is None:
            raise ValueError("stream origin needs a hostname")
        self.host = parsed.hostname
        self.port = parsed.port or 443
        self.path = path
        self.cookie_header = cookie_header
        self.evidence = StreamEvidence()
        self._condition = threading.Condition()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def wait_for(self, predicate, *, timeout: float, label: str) -> None:
        deadline = time.monotonic() + timeout
        with self._condition:
            while not predicate(self.evidence):
                if self.evidence.failure is not None:
                    raise RuntimeError(self.evidence.failure)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"timed out waiting for {label}")
                self._condition.wait(timeout=min(remaining, 1.0))

    def _record_event(self, name: str, data: str) -> None:
        with self._condition:
            if name == "plotting-room-ready":
                self.evidence.ready_count += 1
            elif name == "pounce.worker.draining":
                self.evidence.draining_count += 1
            elif name == "plotting-room-message":
                for marker in ("before-deploy", "after-deploy"):
                    if marker in data:
                        self.evidence.message_markers.add(marker)
            self._condition.notify_all()

    def _record_reconnect_failure(self) -> None:
        with self._condition:
            self.evidence.reconnect_failures += 1
            self._condition.notify_all()

    def _fail(self, exc: BaseException) -> None:
        with self._condition:
            self.evidence.failure = f"plotting stream failed: {type(exc).__name__}"
            self._condition.notify_all()

    def _run(self) -> None:
        context = ssl.create_default_context()
        try:
            while not self._stop.is_set():
                connection = http.client.HTTPSConnection(
                    self.host,
                    self.port,
                    timeout=45,
                    context=context,
                )
                try:
                    connection.request(
                        "GET",
                        self.path,
                        headers={
                            "Accept": "text/event-stream",
                            "Cache-Control": "no-cache",
                            "Cookie": self.cookie_header,
                            "User-Agent": "elbysodic-railway-drain-smoke/1",
                        },
                    )
                    response = connection.getresponse()
                    if response.status != 200:
                        self._record_reconnect_failure()
                        continue
                    event_name = "message"
                    data_lines: list[str] = []
                    while not self._stop.is_set():
                        raw_line = response.readline()
                        if not raw_line:
                            break
                        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                        if not line:
                            self._record_event(event_name, "\n".join(data_lines))
                            if event_name == "pounce.worker.draining":
                                break
                            event_name = "message"
                            data_lines = []
                        elif line.startswith("event:"):
                            event_name = line[6:].strip()
                        elif line.startswith("data:"):
                            data_lines.append(line[5:].lstrip())
                except OSError, TimeoutError:
                    self._record_reconnect_failure()
                finally:
                    connection.close()
                if not self._stop.wait(0.5):
                    continue
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            self._fail(exc)


def _require_staging(origin: str, *, confirmed: bool) -> str:
    normalized = origin.rstrip("/")
    if normalized != STAGING_ORIGIN:
        raise RuntimeError(f"drain smoke is pinned to {STAGING_ORIGIN}")
    if not confirmed:
        raise RuntimeError("drain smoke requires --confirm-staging-write")
    return normalized


def _csrf_token(html: str) -> str:
    match = CSRF_RE.search(html)
    if match is None:
        raise RuntimeError("rendered form did not include a CSRF token")
    return match.group(1)


def _login(origin: str, account: str) -> BrowserSession:
    session = BrowserSession(origin)
    page = session.request("/login")
    if page.status != 200:
        raise RuntimeError(f"login page returned HTTP {page.status}")
    response = session.request(
        "/login",
        form={
            "_csrf_token": _csrf_token(page.text),
            "email": account,
            "password": SEED_LOGIN_PHRASE,
            "next": WANTED_PATH,
        },
    )
    if response.status != 200 or not any(
        cookie.name == SESSION_COOKIE for cookie in session.cookies
    ):
        raise RuntimeError("seeded login did not establish an authenticated session")
    return session


def _plotting_path(html: str) -> str | None:
    matches = PLOTTING_PATH_RE.findall(html)
    return matches[0][0] if matches else None


def _form_for_intent(html: str, intent: str) -> str | None:
    needle = f'name="intent" value="{intent}"'
    return next((form for form in FORM_RE.findall(html) if needle in form), None)


def _hidden_value(form: str, name: str) -> str:
    match = re.search(rf'name="{re.escape(name)}" value="([^"]+)"', form)
    if match is None:
        raise RuntimeError(f"rendered form omitted {name}")
    return match.group(1)


def _prepare_room(origin: str) -> tuple[BrowserSession, str]:
    applicant = _login(origin, APPLICANT_ACCOUNT)
    wanted = applicant.request(WANTED_PATH)
    room_path = _plotting_path(wanted.text)
    if room_path is None:
        interest_form = _form_for_intent(wanted.text, "express_interest")
        if interest_form is not None:
            wanted = applicant.request(
                WANTED_PATH,
                form={
                    "_csrf_token": _csrf_token(interest_form),
                    "intent": "express_interest",
                },
            )
            if wanted.status != 200:
                raise RuntimeError(f"interest write returned HTTP {wanted.status}")

    owner = _login(origin, OWNER_ACCOUNT)
    wanted = owner.request(WANTED_PATH)
    room_path = _plotting_path(wanted.text)
    if room_path is None:
        room_form = _form_for_intent(wanted.text, "start_plotting_room")
        if room_form is None:
            raise RuntimeError("no seeded plotting-room handoff is available")
        room = owner.request(
            WANTED_PATH,
            form={
                "_csrf_token": _csrf_token(room_form),
                "intent": "start_plotting_room",
                "interest_id": _hidden_value(room_form, "interest_id"),
            },
        )
        if room.status != 200:
            raise RuntimeError(f"plotting-room creation returned HTTP {room.status}")
        room_path = urlsplit(room.url).path
    if not re.fullmatch(r"/c/x-men-apocalypse/plotting/\d+", room_path):
        raise RuntimeError("rendered plotting-room path was outside the staging fixture")
    return owner, room_path


def _post_message(session: BrowserSession, room_path: str, marker: str) -> None:
    room = session.request(room_path)
    composer = _form_for_intent(room.text, "post_message")
    if room.status != 200 or composer is None:
        raise RuntimeError("seeded writer cannot open the plotting composer")
    response = session.request(
        room_path,
        form={
            "_csrf_token": _csrf_token(composer),
            "intent": "post_message",
            "body": f"[staging drain smoke] {marker}",
        },
    )
    if response.status != 200:
        raise RuntimeError(f"plotting write returned HTTP {response.status}")


def run(origin: str, *, timeout: float) -> None:
    session, room_path = _prepare_room(origin)
    stream_path = f"{room_path}/stream"
    monitor = PlottingStreamMonitor(origin, stream_path, session.cookie_header())
    monitor.start()
    try:
        monitor.wait_for(lambda item: item.ready_count >= 1, timeout=30, label="initial stream")
        _post_message(session, room_path, "before-deploy")
        monitor.wait_for(
            lambda item: "before-deploy" in item.message_markers,
            timeout=30,
            label="pre-deploy acknowledged write",
        )
        print("drain smoke armed: authenticated_stream=1 acknowledged_writes=1")
        print("trigger one staging-only redeploy now; the helper will wait for worker drain")
        monitor.wait_for(
            lambda item: item.draining_count >= 1,
            timeout=timeout,
            label="pounce.worker.draining",
        )
        monitor.wait_for(
            lambda item: item.ready_count >= 2,
            timeout=180,
            label="replacement stream",
        )
        _post_message(session, room_path, "after-deploy")
        monitor.wait_for(
            lambda item: "after-deploy" in item.message_markers,
            timeout=30,
            label="post-deploy acknowledged write",
        )
        persisted = session.request(room_path)
        if persisted.status != 200 or not all(
            marker in persisted.text for marker in ("before-deploy", "after-deploy")
        ):
            raise RuntimeError("acknowledged plotting writes did not persist across redeploy")
        evidence = monitor.evidence
        print(
            "drain smoke passed: drain_events=1 reconnect_ready=1 "
            f"acknowledged_writes=2 persisted_writes=2 reconnect_failures={evidence.reconnect_failures}"
        )
    finally:
        monitor.stop()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default=STAGING_ORIGIN)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument(
        "--confirm-staging-write",
        action="store_true",
        help="Required; permits fixture-room setup and two staging plotting messages.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    origin = _require_staging(args.origin, confirmed=args.confirm_staging_write)
    run(origin, timeout=max(args.timeout, 60.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
