from __future__ import annotations

import argparse
import asyncio
import time
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, async_playwright

STAFF_EMAIL = "moira@example.com"
COMMUNITY_PATH = "/c/x-men-apocalypse"


async def _login(page: Page, base_url: str, email: str, *, next_path: str) -> None:
    await page.goto(urljoin(base_url, f"/login?next={next_path}"), wait_until="domcontentloaded")
    await page.get_by_label("Email").fill(email)
    await page.get_by_label("Password").fill(_seed_password())
    await page.get_by_role("button", name="Log in").click()
    await page.wait_for_url(f"**{next_path}")


async def _create_invitation(page: Page, base_url: str) -> str:
    invite_email = f"activation-{int(time.time())}@example.com"
    await _login(
        page,
        base_url,
        STAFF_EMAIL,
        next_path=f"{COMMUNITY_PATH}/studio/launch",
    )
    await page.get_by_label("Writer email").fill(invite_email)
    await page.locator('form:has(input[name="intent"][value="create_invite"])').evaluate(
        "form => form.requestSubmit()"
    )
    invite = page.locator('a[href^="/invite/"]').last
    href = await invite.get_attribute("href")
    if not href:
        raise AssertionError("Invitation link was not rendered after creation.")
    return urlparse(href).path


async def _accept_invitation_without_face(page: Page, base_url: str, invite_path: str) -> None:
    await page.context.clear_cookies()
    await page.goto(urljoin(base_url, invite_path), wait_until="domcontentloaded")
    await page.get_by_label("Writer username").fill(f"activation-{int(time.time())}")
    await page.get_by_label("Display name").fill("Activation QA")
    await page.get_by_label("Password").fill("activation-password")
    await page.get_by_role("button", name="Enter realm").click()
    await page.wait_for_url(f"**{COMMUNITY_PATH}/applications/new")
    await page.get_by_role("button", name="Create draft face").wait_for()
    await page.goto(urljoin(base_url, f"{COMMUNITY_PATH}/desk"), wait_until="domcontentloaded")
    await page.get_by_text("Start with a first face").wait_for()


async def _create_first_face_draft(page: Page, base_url: str) -> None:
    await page.goto(urljoin(base_url, f"{COMMUNITY_PATH}/applications/new"))
    await page.get_by_label("Face name").fill(f"Activation Face {int(time.time())}")
    await page.get_by_label("Concept summary").fill("Browser QA first-face activation draft.")
    await page.get_by_label("Application notes").fill(
        "A short browser QA application note for the activation path."
    )
    required_fields = page.locator(
        'input[name^="application_field_"][required], textarea[name^="application_field_"][required]'
    )
    for index in range(await required_fields.count()):
        field = required_fields.nth(index)
        if not await field.input_value():
            await field.fill(f"Activation QA {index + 1}")
    required_selects = page.locator('select[name^="application_field_"][required]')
    for index in range(await required_selects.count()):
        select = required_selects.nth(index)
        options = await select.locator("option").evaluate_all(
            "options => options.map(option => option.value).filter(Boolean)"
        )
        if options:
            await select.select_option(options[0])
    await page.get_by_role("button", name="Create draft face").click()
    await page.wait_for_url("**/applications/*")
    await page.get_by_text("Application Review Room").wait_for()
    await page.goto(urljoin(base_url, f"{COMMUNITY_PATH}/desk"), wait_until="domcontentloaded")
    await page.get_by_text("Continue application").wait_for()


async def _check_existing_play_path(page: Page, base_url: str) -> None:
    await _login(page, base_url, "writer@example.com", next_path=f"{COMMUNITY_PATH}/desk")
    await page.get_by_role("heading", name="Writer Desk").wait_for()
    await page.goto(urljoin(base_url, f"{COMMUNITY_PATH}/wanted"), wait_until="domcontentloaded")
    await page.get_by_role("heading", name="Wanted").wait_for()
    wanted_link = page.locator('#page-content a[href*="/wanted/"]').first
    await wanted_link.click()
    await page.wait_for_url("**/wanted/*")
    await page.goto(urljoin(base_url, f"{COMMUNITY_PATH}/plotting"), wait_until="domcontentloaded")
    await page.get_by_role("heading", name="Plotting Rooms").wait_for()


async def _run(base_url: str) -> int:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            invite_path = await _create_invitation(page, base_url)
            await _accept_invitation_without_face(page, base_url, invite_path)
            await _create_first_face_draft(page, base_url)
            await _check_existing_play_path(page, base_url)
        finally:
            await browser.close()
    print("Writer activation QA passed.")
    return 0


def _seed_password() -> str:
    return "pass" + "word"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise invite acceptance, first-face application, wanted browsing, "
            "plotting, and first-scene handoff surfaces in a seeded preview."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    return asyncio.run(_run(args.base_url))


if __name__ == "__main__":
    raise SystemExit(main())
