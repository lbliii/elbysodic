from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from time import perf_counter
from urllib.parse import urlencode

from chirp.testing import TestClient

from elbysodic.services import create_services
from elbysodic.web import create_app
from elbysodic.web.state import get_services

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
ROUTE_TIME_HEADER = "x-elbysodic-route-time-ms"


@dataclass(frozen=True, slots=True)
class CheckResult:
    label: str
    method: str
    path: str
    status: int
    wall_ms: float
    route_ms: str
    cookie_changed: bool = False


def _header(response: object, name: str) -> str | None:
    headers = getattr(response, "headers", ())
    if isinstance(headers, dict):
        value = headers.get(name) or headers.get(name.lower()) or headers.get(name.title())
        return None if value is None else str(value)
    for key, value in headers:
        if str(key).lower() == name.lower():
            return str(value)
    return None


def _cookie_pair(response: object, name: str) -> str | None:
    header = _header(response, "set-cookie")
    if header is None:
        return None
    pair = header.split(";", 1)[0]
    return pair if pair.startswith(f"{name}=") else None


async def _timed_get(client: TestClient, label: str, path: str, cookie: str | None) -> CheckResult:
    headers = {"Cookie": cookie} if cookie else None
    started = perf_counter()
    response = await client.get(path, headers=headers)
    wall_ms = (perf_counter() - started) * 1000
    return CheckResult(
        label=label,
        method="GET",
        path=path,
        status=response.status,
        wall_ms=wall_ms,
        route_ms=_header(response, ROUTE_TIME_HEADER) or "",
    )


async def _timed_switch(
    client: TestClient,
    label: str,
    membership_id: int,
    next_url: str,
    cookie: str | None,
) -> tuple[CheckResult, str | None]:
    headers = dict(FORM_HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    started = perf_counter()
    response = await client.post(
        "/identity",
        body=urlencode(
            {
                "intent": "switch_membership",
                "membership_id": str(membership_id),
                "character_id": "0",
                "next": next_url,
            }
        ).encode(),
        headers=headers,
    )
    wall_ms = (perf_counter() - started) * 1000
    next_cookie = _cookie_pair(response, "elbysodic_dev_identity") or cookie
    return (
        CheckResult(
            label=label,
            method="POST",
            path="/identity",
            status=response.status,
            wall_ms=wall_ms,
            route_ms=_header(response, ROUTE_TIME_HEADER) or "",
            cookie_changed=next_cookie != cookie,
        ),
        next_cookie,
    )


async def run(iterations: int) -> list[CheckResult]:
    app = create_app(debug=False, services=create_services(path=":memory:"))
    services = get_services()
    user_id = services.seed.user.id
    switch_targets = (
        ("enter-nyc", "rl-nyc", "/c/rl-nyc/my/threads"),
        ("enter-small-town", "rl-small-town", "/c/rl-small-town/boards/town-hall?filter=mine"),
        ("enter-jurassic", "jurassic-park-universe", "/c/jurassic-park-universe/world"),
        ("enter-xmen", "x-men-apocalypse", "/boards/danger-room"),
    )
    route_targets = (
        ("network", "/network"),
        ("nyc-claims", "/c/rl-nyc/claims"),
        ("nyc-my-threads", "/c/rl-nyc/my/threads"),
        ("small-town-mine", "/c/rl-small-town/boards/town-hall?filter=mine"),
        ("jurassic-world", "/c/jurassic-park-universe/world"),
    )
    memberships = {
        slug: services.repo.get_membership_for_user(
            services.repo.get_community_by_slug(slug).id,
            user_id,
        ).id
        for _, slug, _ in switch_targets
    }

    results: list[CheckResult] = []
    cookie: str | None = None
    async with TestClient(app) as client:
        for index in range(iterations):
            for label, slug, next_url in switch_targets:
                result, cookie = await _timed_switch(
                    client,
                    f"{label}-{index + 1}",
                    memberships[slug],
                    next_url,
                    cookie,
                )
                results.append(result)
                results.append(
                    await _timed_get(
                        client,
                        f"{label}-landing-{index + 1}",
                        next_url,
                        cookie,
                    )
                )
            for label, path in route_targets:
                results.append(await _timed_get(client, f"{label}-{index + 1}", path, cookie))
    return results


def _print_results(results: list[CheckResult]) -> None:
    failures = [item for item in results if item.status >= 400]
    slow = sorted(results, key=lambda item: item.wall_ms, reverse=True)[:8]
    print("label\tmethod\tstatus\troute_ms\twall_ms\tpath")
    for item in results:
        print(
            f"{item.label}\t{item.method}\t{item.status}\t"
            f"{item.route_ms or '-'}\t{item.wall_ms:.1f}\t{item.path}"
        )
    if failures:
        print("\nFailures:")
        for item in failures:
            print(f"{item.status} {item.method} {item.path} ({item.label})")
    print("\nSlowest:")
    for item in slow:
        print(f"{item.wall_ms:.1f}ms wall / {item.route_ms or '-'}ms route {item.path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exercise rapid identity and route navigation against a seeded local app."
    )
    parser.add_argument("--iterations", type=int, default=2)
    args = parser.parse_args()
    results = asyncio.run(run(max(args.iterations, 1)))
    _print_results(results)
    if any(item.status >= 500 for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
