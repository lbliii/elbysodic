from __future__ import annotations

import argparse
import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, async_playwright


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int


@dataclass(frozen=True)
class Route:
    label: str
    path: str


VIEWPORTS = (
    Viewport("desktop", 1440, 1200),
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


async def _check_page(page: Page) -> list[str]:
    return await page.evaluate(
        """() => {
          const issues = [];
          const width = document.documentElement.clientWidth;
          if (document.documentElement.scrollWidth > width + 2) {
            issues.push(`document horizontal overflow: ${document.documentElement.scrollWidth}px > ${width}px`);
          }

          const controlSelector = 'a.chirpui-btn, button, .chirpui-chip, .elbysodic-filter-link';
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
            '.elbysodic-thread-card__poster',
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


async def _run(base_url: str, artifact_dir: Path) -> int:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
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
        routes = [*STATIC_ROUTES, *(await _discover_routes(page, base_url))]
        await page.close()

        seen: set[str] = set()
        unique_routes = []
        for route in routes:
            if route.path not in seen:
                unique_routes.append(route)
                seen.add(route.path)

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
            for route in unique_routes:
                url = urljoin(base_url, route.path)
                response = await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(250)
                status = response.status if response else 0
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
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url, Path(args.artifact_dir)))


if __name__ == "__main__":
    raise SystemExit(main())
