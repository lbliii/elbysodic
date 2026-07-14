from __future__ import annotations

import argparse
import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import (
    Page,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int


@dataclass(frozen=True)
class Route:
    label: str
    path: str
    persona_key: str = ""
    next_path: str = ""


VIEWPORTS = (
    Viewport("desktop", 1440, 1200),
    Viewport("tablet", 900, 1100),
    Viewport("mobile", 390, 844),
)

STATIC_ROUTES = (
    Route("home", "/"),
    Route("network", "/network"),
    Route("rl-world", "/c/rl-nyc/world"),
    Route("rl-locations", "/c/rl-nyc/locations"),
    Route("rl-my-threads", "/c/rl-nyc/my/threads"),
    Route("rl-wanted", "/c/rl-nyc/wanted"),
    Route("rl-applications", "/c/rl-nyc/applications"),
    Route("rl-claims", "/c/rl-nyc/claims"),
    Route("rl-studio", "/c/rl-nyc/studio"),
    Route("jp-isla-nublar", "/c/jurassic-park-universe/boards/isla-nublar"),
)

PREMISE_DISCOVERY_ROUTES = (
    Route("home", "/"),
    Route("network", "/network"),
    Route("network-small-town-social-web", "/network?q=small-town+social+web"),
    Route("network-weird-town-mystery", "/network?q=weird-town+mystery"),
    Route("network-court-faction", "/network?q=court+faction"),
    Route("network-strange-frontier", "/network?q=strange+frontier"),
    Route("harbor-society", "/c/harbor-society"),
    Route("signal-creek", "/c/signal-creek"),
    Route("nocturne-row", "/c/nocturne-row"),
    Route("crownfall", "/c/crownfall"),
    Route("afterlight-accord", "/c/afterlight-accord"),
    Route("brightline", "/c/brightline"),
    Route("emberhouse", "/c/emberhouse"),
    Route("gaslight-ward", "/c/gaslight-ward"),
    Route("wayfarer-station", "/c/wayfarer-station"),
    Route("harbor-wanted-detail", "/c/harbor-society/wanted/reporter-source-at-the-club"),
    Route("signal-wanted-detail", "/c/signal-creek/wanted/cult-survivor-who-remembers-1998"),
    Route("wayfarer-wanted-detail", "/c/wayfarer-station/wanted/corporate-auditor"),
    Route("harbor-first-face", "/c/harbor-society/applications/new"),
    Route("signal-first-face", "/c/signal-creek/applications/new"),
    Route("wayfarer-first-face", "/c/wayfarer-station/applications/new"),
    Route("studio-discovery", "/studio/discovery"),
)

COMMUNITY_HUB_ROUTES = (
    Route("network-small-town-social-web", "/network?q=small-town+social+web"),
    Route("network-weird-town-mystery", "/network?q=weird-town+mystery"),
    Route("network-strange-frontier", "/network?q=strange+frontier"),
    Route("harbor-society", "/c/harbor-society"),
    Route("signal-creek", "/c/signal-creek"),
    Route("nocturne-row", "/c/nocturne-row"),
    Route("wayfarer-station", "/c/wayfarer-station"),
)

COMMUNITY_LANDING_ROUTES = (
    Route("afterlight-public", "/c/afterlight-accord"),
    Route("afterlight-search", "/c/afterlight-accord/search?q=seal"),
    Route("afterlight-request-access", "/c/afterlight-accord/request-access"),
    Route(
        "afterlight-account-visitor",
        "/c/afterlight-accord",
        "xmen_staff",
        "/c/afterlight-accord",
    ),
    Route(
        "afterlight-account-search",
        "/c/afterlight-accord/search?q=seal",
        "xmen_staff",
        "/c/afterlight-accord/search?q=seal",
    ),
    Route("xmen-member-home", "/c/x-men-apocalypse", "xmen_staff", "/c/x-men-apocalypse"),
    Route(
        "xmen-first-face",
        "/c/x-men-apocalypse/applications/new",
        "xmen_staff",
        "/c/x-men-apocalypse/applications/new",
    ),
    Route(
        "xmen-accepted-application",
        "/c/x-men-apocalypse/applications/rogue",
        "xmen_staff",
        "/c/x-men-apocalypse/applications/rogue",
    ),
    Route(
        "xmen-studio-operations",
        "/c/x-men-apocalypse/studio/operations",
        "xmen_staff",
        "/c/x-men-apocalypse/studio/operations",
    ),
    Route(
        "xmen-studio-launch",
        "/c/x-men-apocalypse/studio/launch",
        "xmen_staff",
        "/c/x-men-apocalypse/studio/launch",
    ),
)

DEEP_SEED_ROUTES = (
    Route("home", "/"),
    Route("network", "/network"),
    Route("rl-world", "/c/rl-nyc/world"),
    Route("rl-locations", "/c/rl-nyc/locations"),
    Route("rl-my-threads", "/c/rl-nyc/my/threads"),
    Route("rl-wanted", "/c/rl-nyc/wanted"),
    Route("rl-applications", "/c/rl-nyc/applications"),
    Route("rl-applications-new", "/c/rl-nyc/applications/new"),
    Route("rl-claims", "/c/rl-nyc/claims"),
    Route("rl-casting", "/c/rl-nyc/casting"),
    Route("rl-characters", "/c/rl-nyc/characters"),
    Route("rl-community", "/c/rl-nyc/community"),
    Route("rl-desk", "/c/rl-nyc/desk"),
    Route("rl-discover", "/c/rl-nyc/discover"),
    Route("rl-plotting", "/c/rl-nyc/plotting"),
    Route("rl-studio", "/c/rl-nyc/studio"),
    Route("rl-studio-intake", "/c/rl-nyc/studio/intake"),
    Route("rl-studio-operations", "/c/rl-nyc/studio/operations"),
    Route("rl-shift-work", "/c/rl-nyc/boards/shift-work"),
    Route("rl-shift-work-composer", "/c/rl-nyc/boards/shift-work/threads/new"),
    Route("jp-world", "/c/jurassic-park-universe/world"),
    Route("jp-world-premise", "/c/jurassic-park-universe/world/premise"),
    Route("jp-world-park-status", "/c/jurassic-park-universe/world/park-status"),
    Route("jp-locations", "/c/jurassic-park-universe/locations"),
    Route("jp-isla-nublar", "/c/jurassic-park-universe/boards/isla-nublar"),
    Route("jp-control-room", "/c/jurassic-park-universe/boards/control-room"),
    Route("jp-control-room-composer", "/c/jurassic-park-universe/boards/control-room/threads/new"),
    Route("jp-my-threads", "/c/jurassic-park-universe/my/threads"),
    Route("jp-wanted", "/c/jurassic-park-universe/wanted"),
    Route("jp-studio", "/c/jurassic-park-universe/studio"),
)

DEEP_LINK_PATTERNS = (
    "/applications",
    "/boards/",
    "/casting",
    "/characters/",
    "/claims",
    "/community",
    "/desk",
    "/discover",
    "/locations",
    "/members/",
    "/my/threads",
    "/plotting",
    "/studio",
    "/threads/",
    "/wanted/",
    "/world/",
)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip("/").lower()).strip("-")
    return slug or "home"


async def _first_href(page: Page, selector: str) -> str | None:
    locator = page.locator(selector)
    count = await locator.count()
    for index in range(count):
        href = await locator.nth(index).get_attribute("href")
        if href:
            return href
    return None


async def _discover_routes(page: Page, base_url: str) -> list[Route]:
    routes: list[Route] = []
    await page.goto(urljoin(base_url, "/c/rl-nyc/locations"), wait_until="domcontentloaded")
    await page.wait_for_timeout(250)

    board_href = await _first_href(page, 'a[href*="/boards/"]:not([href*="/threads/"])')
    if board_href:
        board_path = urlparse(board_href).path
        routes.append(Route("rl-board-discovered", board_path))
        await page.goto(urljoin(base_url, board_path), wait_until="domcontentloaded")
        await page.wait_for_timeout(250)

        thread_href = await _first_href(page, 'a[href*="/threads/"]:not([href$="/threads/new"])')
        if thread_href:
            routes.append(Route("rl-thread-discovered", urlparse(thread_href).path))

        composer_href = await _first_href(page, 'a[href$="/threads/new"]')
        if composer_href:
            routes.append(Route("rl-composer-discovered", urlparse(composer_href).path))

    await page.goto(urljoin(base_url, "/c/rl-nyc/wanted"), wait_until="domcontentloaded")
    await page.wait_for_timeout(250)
    wanted_href = await _first_href(page, 'a[href*="/wanted/"]')
    if wanted_href:
        routes.append(Route("rl-wanted-detail-discovered", urlparse(wanted_href).path))

    return routes


async def _discover_deep_routes(page: Page, base_url: str) -> list[Route]:
    discovered: list[Route] = []
    seen: set[str] = set()

    async def add(label: str, path: str) -> None:
        if path in seen or path.startswith(("/logout", "/identity", "/mentionables")):
            return
        seen.add(path)
        discovered.append(Route(label, path))

    for route in DEEP_SEED_ROUTES:
        await add(route.label, route.path)
        response = await page.goto(urljoin(base_url, route.path), wait_until="domcontentloaded")
        await page.wait_for_timeout(200)
        if response and response.status >= 400:
            continue

        hrefs = await page.locator("a[href]").evaluate_all(
            """links => links
              .map(link => link.getAttribute('href'))
              .filter(Boolean)
            """
        )
        for href in hrefs:
            path = urlparse(href).path
            if not path:
                continue
            if any(pattern in path for pattern in DEEP_LINK_PATTERNS):
                await add(f"deep-{len(discovered) + 1:02d}", path)

    return discovered


async def _check_page(page: Page) -> list[str]:
    return await page.evaluate(
        """() => {
          const issues = [];
          const width = document.documentElement.clientWidth;
          if (document.documentElement.scrollWidth > width + 2) {
            issues.push(`document horizontal overflow: ${document.documentElement.scrollWidth}px > ${width}px`);
          }

          const controlSelector = 'a.chirpui-btn, button, .chirpui-chip, .elbysodic-filter-link, .chirpui-sidebar__link';
          for (const el of Array.from(document.querySelectorAll(controlSelector))) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && el.scrollWidth > el.clientWidth + 2) {
              issues.push(`control text overflow: ${el.tagName.toLowerCase()}.${el.className}`);
              break;
            }
          }

          const mediaSelector = [
            '.elbysodic-board-stage',
            '.elbysodic-board-poster',
            '.elbysodic-material-hero',
            '.elbysodic-thread-card__poster',
            '.elbysodic-wanted-card',
            '.elbysodic-network-card__poster',
            '.elbysodic-profile-hero__poster',
            '.elbysodic-post__poster-media'
          ].join(',');

          for (const el of Array.from(document.querySelectorAll(mediaSelector))) {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) continue;
            const style = getComputedStyle(el);
            const hasBackground = style.backgroundImage && style.backgroundImage !== 'none';
            const img = el.querySelector('img');
            const hasLoadedImage = !img || img.complete;
            if (!hasBackground && !img) {
              issues.push(`media without visual fill: ${el.className}`);
              break;
            }
            if (!hasLoadedImage) {
              issues.push(`media image not loaded: ${img.getAttribute('src') || ''}`);
              break;
            }
            if (rect.width < 24 || rect.height < 24) {
              issues.push(`media too small: ${el.className} ${Math.round(rect.width)}x${Math.round(rect.height)}`);
              break;
            }
          }

          const topbar = document.querySelector('.chirpui-app-shell__topbar');
          if (topbar) {
            const rect = topbar.getBoundingClientRect();
            const maxTopbarHeight = window.innerWidth < 640 ? 128 : 76;
            if (rect.height > maxTopbarHeight) {
              issues.push(`topbar unusually tall: ${Math.round(rect.height)}px`);
            }
          }

          for (const el of Array.from(document.querySelectorAll('h1, h2, h3, .elbysodic-copy-lead, .elbysodic-prose-body'))) {
            if (el.classList.contains('elbysodic-visually-hidden')) continue;
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && el.scrollWidth > el.clientWidth + 2) {
              const range = document.createRange();
              range.selectNodeContents(el);
              const textRect = range.getBoundingClientRect();
              const branch = el.parentElement;
              const layout = branch?.parentElement;
              const collides = Array.from(layout?.children || []).some(sibling => {
                if (sibling === branch) return false;
                const siblingRange = document.createRange();
                siblingRange.selectNodeContents(sibling);
                const siblingRect = siblingRange.getBoundingClientRect();
                return textRect.left < siblingRect.right - 2
                  && textRect.right > siblingRect.left + 2
                  && textRect.top < siblingRect.bottom - 2
                  && textRect.bottom > siblingRect.top + 2;
              });
              if (collides) {
                issues.push(`text collision: ${el.tagName.toLowerCase()}.${el.className}`);
                break;
              }
            }
          }

          return issues;
        }"""
    )


async def _hide_debug_overlays(page: Page) -> None:
    await page.add_style_tag(
        content="""
          #chirp-debug,
          .chirp-dbg-pill,
          .chirp-dbg-drawer {
            display: none !important;
          }
        """
    )


async def _switch_dev_persona(
    page: Page,
    base_url: str,
    *,
    persona_key: str,
    next_path: str,
) -> str | None:
    response = await page.goto(urljoin(base_url, "/dev/personas"), wait_until="domcontentloaded")
    if response and response.status >= 400:
        return f"dev persona switcher failed: HTTP {response.status}"

    form = page.locator(f'form:has(input[name="persona_key"][value="{persona_key}"])').first
    if await form.count() == 0:
        return f"dev persona switch failed: missing form for {persona_key}"
    await form.locator('input[name="next"]').evaluate(
        "(input, value) => input.value = value", next_path
    )
    try:
        async with page.expect_navigation(wait_until="domcontentloaded") as navigation:
            await form.locator('button[type="submit"]').click()
        response = await navigation.value
    except PlaywrightTimeoutError:
        return f"dev persona switch failed: timeout for {persona_key}"
    if response and response.status >= 400:
        return f"dev persona switch failed: HTTP {response.status} for {persona_key}"
    return None


async def _run(base_url: str, artifact_dir: Path, profile: str) -> int:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    skipped: list[str] = []
    console_errors: list[str] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        if profile == "deep":
            routes = await _discover_deep_routes(page, base_url)
        elif profile == "premise":
            routes = list(PREMISE_DISCOVERY_ROUTES)
        elif profile == "community-hub":
            routes = list(COMMUNITY_HUB_ROUTES)
        elif profile == "community-landing":
            routes = list(COMMUNITY_LANDING_ROUTES)
        else:
            routes = [*STATIC_ROUTES, *(await _discover_routes(page, base_url))]
        await page.close()

        seen: set[str] = set()
        unique_routes = []
        for route in routes:
            route_key = f"{route.persona_key}:{route.path}"
            if route_key not in seen:
                unique_routes.append(route)
                seen.add(route_key)

        for viewport in VIEWPORTS:
            context = await browser.new_context(
                viewport={"width": viewport.width, "height": viewport.height},
                device_scale_factor=1,
            )
            page = await context.new_page()
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text) if message.type == "error" else None
                ),
            )
            if profile == "premise":
                switch_error = await _switch_dev_persona(
                    page,
                    base_url,
                    persona_key="harbor_director",
                    next_path="/studio/discovery",
                )
                if switch_error:
                    failures.append(f"{viewport.name}: {switch_error}")
                    await context.close()
                    continue
            for route in unique_routes:
                if route.persona_key:
                    switch_error = await _switch_dev_persona(
                        page,
                        base_url,
                        persona_key=route.persona_key,
                        next_path=route.next_path or route.path,
                    )
                    if switch_error:
                        failures.append(f"{viewport.name} {route.label}: {switch_error}")
                        continue
                url = urljoin(base_url, route.path)
                response = await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(250)
                status = response.status if response else 0
                if status in (401, 403):
                    skipped.append(f"{viewport.name} {route.label}: HTTP {status} at {route.path}")
                    continue
                if status >= 400 or status == 0:
                    failures.append(f"{viewport.name} {route.label}: HTTP {status} at {route.path}")
                    continue
                await _hide_debug_overlays(page)

                screenshot = artifact_dir / f"{viewport.name}-{route.label}-{_slug(route.path)}.png"
                await page.screenshot(path=screenshot, full_page=True)

                failures.extend(
                    f"{viewport.name} {route.label}: {issue}" for issue in await _check_page(page)
                )
            await context.close()

        await browser.close()

    print(f"Browser QA screenshots: {artifact_dir}")
    if skipped:
        print("Skipped protected routes:")
        for message in skipped[:12]:
            print(f"- {message}")
    if console_errors:
        print("Console errors:")
        for message in console_errors[:12]:
            print(f"- {message}")
    if failures:
        print("Browser QA failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Browser QA passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Elbysodic browser visual smoke QA.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8003")
    parser.add_argument("--artifact-dir", default="tests/browser/artifacts")
    parser.add_argument(
        "--profile",
        choices=("smoke", "deep", "premise", "community-hub", "community-landing"),
        default="smoke",
    )
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url, Path(args.artifact_dir), args.profile))


if __name__ == "__main__":
    raise SystemExit(main())
