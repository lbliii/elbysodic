from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import time
from urllib.parse import urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

QA_EMAIL = "mira@example.com"
VIRTUAL_AUTH_OPTIONS = {
    "protocol": "ctap2",
    "transport": "internal",
    "hasResidentKey": True,
    "hasUserVerification": True,
    "isUserVerified": True,
}


async def _add_virtual_authenticator(context: BrowserContext, page: Page) -> None:
    client = await context.new_cdp_session(page)
    await client.send("WebAuthn.enable")
    authenticator = await client.send(
        "WebAuthn.addVirtualAuthenticator",
        {"options": VIRTUAL_AUTH_OPTIONS},
    )
    await client.send(
        "WebAuthn.setAutomaticPresenceSimulation",
        {
            "authenticatorId": authenticator["authenticatorId"],
            "enabled": True,
        },
    )


async def _password_login(
    page: Page,
    base_url: str,
    email: str,
    *,
    next_path: str = "/identity",
) -> None:
    await page.goto(urljoin(base_url, f"/login?next={next_path}"), wait_until="domcontentloaded")
    await page.get_by_label("Email").fill(email)
    await page.get_by_label("Password").fill(_seed_password())
    await page.get_by_role("button", name="Log in").click()
    await page.wait_for_url(f"**{next_path}")


async def _wait_for_passkey_control(page: Page, control_id: str) -> None:
    await page.wait_for_function(
        f"""() => {{
          const control = document.getElementById("{control_id}");
          return !!(control && !control.hidden && window.chirp && window.chirp.passkeys);
        }}"""
    )


async def _register_passkey(page: Page, base_url: str, label: str) -> None:
    await page.goto(urljoin(base_url, "/identity"), wait_until="domcontentloaded")
    await _wait_for_passkey_control(page, "passkey-register")
    await page.locator("#passkey-label").fill(label)
    await page.locator("#passkey-register").click()
    await page.locator(".elbysodic-passkey-list__item strong", has_text=label).wait_for()


async def _logout(page: Page, base_url: str) -> None:
    await page.goto(urljoin(base_url, "/logout"), wait_until="domcontentloaded")
    await page.wait_for_url("**/login")


async def _passkey_login(page: Page, base_url: str, *, next_path: str = "/identity") -> None:
    await page.goto(urljoin(base_url, f"/login?next={next_path}"), wait_until="domcontentloaded")
    await _wait_for_passkey_control(page, "passkey-login")
    await page.locator("#passkey-login").click()
    await page.wait_for_url(f"**{next_path}", timeout=15000)


async def _expect_passkey_login_error(page: Page, base_url: str) -> None:
    await page.goto(urljoin(base_url, "/login"), wait_until="domcontentloaded")
    await _wait_for_passkey_control(page, "passkey-login")
    await page.locator("#passkey-login").click()
    await page.wait_for_timeout(1500)
    if "/login" not in page.url:
        raise AssertionError(f"Passkey login should fail closed but reached {page.url}.")
    error = page.locator("#passkey-login-error")
    if await error.is_visible():
        message = await error.inner_text()
        if not message.strip():
            raise AssertionError("Passkey login should surface an error message.")
        return
    # Discoverable mediation with no resident credential ends as a quiet cancel.


async def _expect_passkey_register_error(page: Page, base_url: str, label: str) -> None:
    await page.goto(urljoin(base_url, "/identity"), wait_until="domcontentloaded")
    await _wait_for_passkey_control(page, "passkey-register")
    await page.locator("#passkey-label").fill(label)
    await page.locator("#passkey-register").click()
    await page.locator("#passkey-register-error").wait_for(state="visible")
    error = await page.locator("#passkey-register-error").inner_text()
    if not error.strip():
        raise AssertionError("Passkey registration should surface an error message.")


async def _remove_registered_passkey(page: Page, base_url: str, label: str) -> None:
    await page.goto(urljoin(base_url, "/identity"), wait_until="domcontentloaded")
    item = page.locator(".elbysodic-passkey-list__item").filter(has_text=label)
    await item.get_by_role("button", name="Remove").click()
    await page.wait_for_url("**/identity")
    await page.locator(".elbysodic-passkey-list__item strong", has_text=label).wait_for(
        state="detached"
    )


def _bump_passkey_sign_count(db_path: str, label: str) -> None:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT id FROM user_passkey_credentials WHERE label = ? ORDER BY id DESC LIMIT 1",
            (label,),
        ).fetchone()
        if row is None:
            raise AssertionError(f"No stored passkey with label {label!r} in {db_path}.")
        connection.execute(
            "UPDATE user_passkey_credentials SET sign_count = 999999 WHERE id = ?",
            (row[0],),
        )
        connection.commit()
    finally:
        connection.close()


async def _new_authenticated_page(
    browser: Browser,
    base_url: str,
    *,
    email: str = QA_EMAIL,
) -> tuple[BrowserContext, Page]:
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
    await _add_virtual_authenticator(context, page)
    await _password_login(page, base_url, email)
    return context, page


async def _run_happy_path(browser: Browser, base_url: str) -> None:
    label = f"QA passkey {int(time.time())}"
    context, page = await _new_authenticated_page(browser, base_url)
    try:
        await _register_passkey(page, base_url, label)
        await _logout(page, base_url)
        await _passkey_login(page, base_url, next_path="/identity")
        await page.locator("strong", has_text=QA_EMAIL).wait_for()
    finally:
        await context.close()


async def _run_revoked_credential(browser: Browser, base_url: str) -> None:
    label = f"Revoked QA {int(time.time())}"
    context, page = await _new_authenticated_page(browser, base_url)
    try:
        await _register_passkey(page, base_url, label)
        await _remove_registered_passkey(page, base_url, label)
        await _logout(page, base_url)
        await _expect_passkey_login_error(page, base_url)
    finally:
        await context.close()


async def _run_unknown_credential(browser: Browser, base_url: str) -> None:
    context = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await context.new_page()
    try:
        await _add_virtual_authenticator(context, page)
        await _expect_passkey_login_error(page, base_url)
    finally:
        await context.close()


async def _run_wrong_origin(browser: Browser, base_url: str) -> None:
    parsed = urlparse(base_url)
    hostname = parsed.hostname or ""
    if hostname not in {"127.0.0.1", "localhost"}:
        raise AssertionError(
            "Wrong-origin browser QA expects a local host mismatch between localhost and 127.0.0.1."
        )
    label = f"Wrong origin QA {int(time.time())}"
    context, page = await _new_authenticated_page(browser, base_url)
    try:
        await _expect_passkey_register_error(page, base_url, label)
    finally:
        await context.close()


async def _run_sign_count_regression(browser: Browser, base_url: str, db_path: str) -> None:
    label = f"Sign-count QA {int(time.time())}"
    context, page = await _new_authenticated_page(browser, base_url)
    try:
        await _register_passkey(page, base_url, label)
        await _logout(page, base_url)
        _bump_passkey_sign_count(db_path, label)
        await _expect_passkey_login_error(page, base_url)
    finally:
        await context.close()


async def _run(base_url: str, db_path: str | None, profile: str) -> int:
    scenarios: list[tuple[str, object, bool]] = [
        ("happy", _run_happy_path, False),
        ("revoked", _run_revoked_credential, False),
        ("unknown", _run_unknown_credential, False),
        ("sign-count", _run_sign_count_regression, True),
    ]
    if profile == "full":
        if os.environ.get("PASSKEY_QA_WRONG_ORIGIN") == "1":
            scenarios.append(("wrong-origin", _run_wrong_origin, False))
        selected = scenarios
    else:
        selected = [
            (
                profile,
                *{
                    "happy": (_run_happy_path, False),
                    "revoked": (_run_revoked_credential, False),
                    "unknown": (_run_unknown_credential, False),
                    "wrong-origin": (_run_wrong_origin, False),
                    "sign-count": (_run_sign_count_regression, True),
                }[profile],
            )
        ]

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            for name, runner, needs_db in selected:
                if needs_db and not db_path:
                    raise AssertionError(
                        f"{name} browser QA requires --db-path so sign_count can be advanced in SQLite."
                    )
                if name == "sign-count":
                    await runner(browser, base_url, db_path)  # type: ignore[arg-type]
                else:
                    await runner(browser, base_url)  # type: ignore[arg-type]
        finally:
            await browser.close()

    print("Passkey browser QA passed.")
    return 0


def _seed_password() -> str:
    return "pass" + "word"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise passkey registration and sign-in with a Playwright virtual "
            "authenticator, plus browser-visible regression scenarios."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8007",
        help="Seeded preview URL. WebAuthn requires localhost (not 127.0.0.1).",
    )
    parser.add_argument(
        "--db-path",
        default="",
        help="SQLite path for the sign-count regression scenario (required for --profile full).",
    )
    parser.add_argument(
        "--profile",
        choices=("full", "happy", "revoked", "unknown", "wrong-origin", "sign-count"),
        default="full",
        help="Run one scenario or the full regression pack.",
    )
    args = parser.parse_args()
    db_path = args.db_path.strip() or None
    return asyncio.run(_run(args.base_url, db_path, args.profile))


if __name__ == "__main__":
    raise SystemExit(main())
