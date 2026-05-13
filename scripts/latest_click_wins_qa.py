from __future__ import annotations

import argparse
import asyncio
from urllib.parse import urljoin

from playwright.async_api import async_playwright

TARGETS = (
    ("/network", "Studio Network"),
    ("/c/rl-nyc/my/threads", "RL NYC"),
    ("/c/rl-small-town/boards/town-hall?filter=mine", "RL Small Town"),
    ("/c/jurassic-park-universe/world", "Jurassic Park Universe"),
    ("/c/x-men-apocalypse/boards/danger-room", "Danger Room"),
)


async def _run(base_url: str) -> int:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            await page.goto(urljoin(base_url, "/"), wait_until="domcontentloaded")
            await page.wait_for_function("window.htmx !== undefined")
            await page.evaluate(
                """
                async (targets) => {
                  for (const target of targets) {
                    window.htmx.ajax("GET", target[0], {
                      target: "#page-content",
                      swap: "innerHTML"
                    });
                  }
                }
                """,
                TARGETS,
            )
            await page.wait_for_function(
                "document.body && document.body.innerText.includes('Danger Room')"
            )
            body_text = await page.locator("body").inner_text()
        finally:
            await browser.close()

    failures = [
        expected
        for _path, expected in TARGETS[:-1]
        if expected in body_text and expected != TARGETS[-1][1]
    ]
    if failures:
        print(f"Latest-click-wins failed; stale content remained: {', '.join(failures)}")
        return 1
    print("Latest-click-wins QA passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify rapid htmx navigations settle on the last requested route."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url))


if __name__ == "__main__":
    raise SystemExit(main())
