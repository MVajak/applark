"""Headless-Chromium scraper for job postings."""

import re
from typing import cast

from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import (
    async_playwright,
)

_EXTRACT_JS = """() => {
    const main = document.querySelector('main') || document.querySelector('article');
    if (main && main.innerText && main.innerText.trim().length > 200) {
        return main.innerText;
    }
    const body = document.body.cloneNode(true);
    ['nav', 'footer', 'header', 'script', 'style', 'aside', 'noscript', 'iframe']
        .forEach(tag => {
            body.querySelectorAll(tag).forEach(el => el.remove());
        });
    return body.innerText;
}"""


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def scrape_job_posting(url: str) -> str:
    """Scrape the main text content of a job posting URL.

    Launches a fresh headless Chromium per call — simpler than maintaining a
    long-lived browser, and a job posting is a one-shot fetch anyway.
    Prefers <main>/<article> content; falls back to <body> with navigation
    chrome filtered out. Raises ``RuntimeError`` on timeout, navigation
    failure, or empty content.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            # Don't wait for "networkidle" — analytics-heavy SPAs like
            # LinkedIn keep firing tracking pings forever and never reach
            # idle. DOMContentLoaded resolves as soon as the HTML is
            # parsed; we then wait for the content selector we actually
            # care about so we don't extract before SPA hydration.
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(f"Timed out loading {url}: {exc}") from exc
            except PlaywrightError as exc:
                raise RuntimeError(f"Navigation error for {url}: {exc}") from exc

            # Most job boards render into <main> or <article>. If neither
            # shows up, fall through and let the <body> fallback in
            # _EXTRACT_JS handle it — but give the page a brief moment
            # to hydrate first.
            try:
                await page.wait_for_selector(
                    "main, article, [role='main']",
                    state="visible",
                    timeout=8_000,
                )
            except PlaywrightTimeoutError:
                await page.wait_for_timeout(1_500)

            raw = cast(str, await page.evaluate(_EXTRACT_JS))
            text = _collapse_whitespace(raw)

            if not text:
                raise RuntimeError(f"Scraped page produced no usable text: {url}")

            return text
        finally:
            await browser.close()
