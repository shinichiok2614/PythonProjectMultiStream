import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError

URLS = [
    "https://aznudelive.com/___Lily___",
]

PROFILE_DIR = "browser_profile"
SAVE_DIR = "screenshots"
INTERVAL = 5

os.makedirs(SAVE_DIR, exist_ok=True)

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=True,
            args=["--mute-audio"]
        )

        pages = []

        for url in URLS:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # ⏱️ Đợi button xác nhận xuất hiện (nếu có)
            try:
                await page.wait_for_selector(
                    "button.btn-visitors-agreement-accept",
                    timeout=5000
                )
                print("👉 Found age confirm button, clicking...")
                await page.click("button.btn-visitors-agreement-accept")
                await asyncio.sleep(2)
            except TimeoutError:
                # Không thấy button → đã xác nhận từ trước
                print("✔ No confirm needed")

            pages.append(page)

        round_idx = 1
        while True:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, page in enumerate(pages):
                out = f"{SAVE_DIR}/site{i+1}_round{round_idx}_{ts}.png"
                await page.screenshot(path=out)
                print("📸", out)

            round_idx += 1
            await asyncio.sleep(INTERVAL)

asyncio.run(main())
