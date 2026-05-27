#!/usr/bin/env python3
"""Capture full screenshots of EPMS UI for documentation and delivery."""

from __future__ import annotations

import asyncio
import html
import os
from pathlib import Path

from playwright.async_api import Page, async_playwright

PORT = int(os.environ.get("EPMS_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"
OUT = Path(os.environ.get("EPMS_SCREENSHOT_DIR", "/opt/cursor/artifacts/screenshots"))


async def load_enterprise_demo(page: Page) -> None:
    try:
        async with page.expect_response(
            lambda r: "/api/demo/reset" in r.url and r.status == 200,
            timeout=15000,
        ):
            await page.click("#loadDemo")
    except Exception:
        await page.request.post(f"{BASE}/api/demo/reset")
    await page.wait_for_timeout(1200)


async def screenshot_element(page: Page, selector: str, path: Path) -> bool:
    loc = page.locator(selector).first
    if await loc.count() == 0:
        return False
    await page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (el) el.scrollIntoView({ block: 'start', behavior: 'instant' });
        }""",
        selector,
    )
    await page.wait_for_timeout(500)
    box = await loc.bounding_box()
    if not box or box["width"] < 8 or box["height"] < 8:
        return False
    try:
        await loc.screenshot(path=str(path), timeout=10_000)
    except Exception:
        await page.screenshot(path=str(path), clip=box)
    return True


async def screenshot_main_viewport(page: Page, path: Path) -> None:
    main = page.locator("main").first
    if await main.count():
        await main.screenshot(path=str(path))
    else:
        await page.screenshot(path=str(path), full_page=False)


async def goto_dashboard(page: Page, lang: str) -> None:
    await page.add_init_script(
        f'localStorage.setItem("epms-language", "{lang}");'
    )
    await page.goto(f"{BASE}/", wait_until="networkidle")
    await page.evaluate(f'localStorage.setItem("epms-language", "{lang}");')
    await page.reload(wait_until="networkidle")
    await page.wait_for_timeout(800)
    await load_enterprise_demo(page)
    await page.wait_for_timeout(600)


def write_gallery(out: Path, items: list[tuple[str, str, str]]) -> None:
    """items: (filename, title_ar, title_en)"""
    rows = []
    for fname, title_ar, title_en in items:
        if not (out / fname).is_file():
            continue
        title = f"{title_en} / {title_ar}"
        rows.append(
            f'<figure><img src="{html.escape(fname)}" alt="{html.escape(title)}" />'
            f"<figcaption>{html.escape(title)}</figcaption></figure>"
        )
    gallery = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <title>EPMS — لقطات النظام</title>
  <style>
    body {{ font-family: system-ui, "Noto Sans Arabic", sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
    header {{ padding: 1.5rem 2rem; background: linear-gradient(135deg,#0ea5a4,#2563eb); }}
    h1 {{ margin: 0; font-size: 1.5rem; }}
    p {{ margin: 0.5rem 0 0; opacity: 0.9; }}
    .grid {{ display: grid; gap: 1.5rem; padding: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }}
    figure {{ margin: 0; background: #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.35); }}
    img {{ width: 100%; display: block; border-bottom: 1px solid #334155; }}
    figcaption {{ padding: 0.75rem 1rem; font-size: 0.9rem; line-height: 1.4; }}
  </style>
</head>
<body>
  <header>
    <h1>Extreme Print Management System</h1>
    <p>لقطات شاشة كاملة — لوحة التحكم، الأقسام، محطة التحرير (EN/AR)</p>
  </header>
  <div class="grid">
    {"".join(rows)}
  </div>
</body>
</html>
"""
    (out / "index.html").write_text(gallery, encoding="utf-8")


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog: list[tuple[str, str, str]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # --- English full dashboard ---
        await goto_dashboard(page, "en")
        await page.screenshot(path=str(OUT / "01-dashboard-full-en.png"), full_page=True)
        catalog.append(("01-dashboard-full-en.png", "لوحة كاملة (إنجليزي)", "Full dashboard (EN)"))
        print("01-dashboard-full-en.png")

        await screenshot_main_viewport(page, OUT / "02-dashboard-viewport-en.png")
        catalog.append(("02-dashboard-viewport-en.png", "منطقة المحتوى (إنجليزي)", "Main viewport (EN)"))

        sections_en = [
            ("#command", "03-command-center-en.png", "مركز القيادة", "Command Center"),
            (".control-panel", "04-policy-simulator-en.png", "محاكي السياسات", "Policy simulator"),
            ("#fleet", "05-fleet-users-printers-en.png", "الأسطول والمستخدمون", "Fleet & users"),
            ("#jobs", "06-secure-jobs-en.png", "مهام الطباعة الآمنة", "Secure jobs"),
            ("#agents", "07-agents-readiness-en.png", "الوكلاء والجاهزية", "Agents & readiness"),
            ("#reports", "08-reports-intelligence-en.png", "التقارير والذكاء", "Reports"),
        ]
        for selector, fname, ar, en in sections_en:
            if await screenshot_element(page, selector, OUT / fname):
                catalog.append((fname, ar, en))
                print(fname)

        # --- Arabic full dashboard ---
        await goto_dashboard(page, "ar")
        await page.screenshot(path=str(OUT / "09-dashboard-full-ar.png"), full_page=True)
        catalog.append(("09-dashboard-full-ar.png", "لوحة كاملة (عربي)", "Full dashboard (AR)"))
        print("09-dashboard-full-ar.png")

        sections_ar = [
            ("#command", "10-command-center-ar.png", "مركز القيادة", "Command Center (AR)"),
            ("#jobs", "11-secure-jobs-ar.png", "مهام آمنة", "Secure jobs (AR)"),
            ("#reports", "12-reports-intelligence-ar.png", "التقارير", "Reports (AR)"),
        ]
        for selector, fname, ar, en in sections_ar:
            if await screenshot_element(page, selector, OUT / fname):
                catalog.append((fname, ar, en))
                print(fname)

        # --- Nav-focused views (click sidebar) ---
        await goto_dashboard(page, "en")
        for href, fname, ar, en in [
            ("#jobs", "13-nav-secure-jobs-en.png", "قسم المهام (تنقل)", "Nav: Secure Jobs"),
            ("#fleet", "14-nav-fleet-en.png", "قسم الأسطول", "Nav: Fleet"),
            ("#agents", "15-nav-agents-en.png", "قسم الوكلاء", "Nav: Agents"),
        ]:
            await page.locator(f'nav a[href="{href}"]').click()
            await page.wait_for_timeout(500)
            await screenshot_main_viewport(page, OUT / fname)
            catalog.append((fname, ar, en))
            print(fname)

        # --- Release station ---
        await page.goto(f"{BASE}/release", wait_until="networkidle")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(OUT / "16-release-station-login.png"), full_page=True)
        catalog.append(("16-release-station-login.png", "محطة التحرير — تسجيل", "Release Station login"))
        print("16-release-station-login.png")

        await page.fill("#username", "student-a")
        await page.click("#load-held")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "17-release-station-held-jobs.png"), full_page=True)
        catalog.append(("17-release-station-held-jobs.png", "مهام معلّقة", "Release Station held jobs"))
        print("17-release-station-held-jobs.png")

        await browser.close()

    write_gallery(OUT, catalog)
    print(f"Gallery: {OUT / 'index.html'}")
    print(f"Total PNG files: {len(list(OUT.glob('*.png')))}")


if __name__ == "__main__":
    asyncio.run(main())
