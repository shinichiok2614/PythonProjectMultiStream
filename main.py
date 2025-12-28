import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError

URLS = [
    "https://aznudelive.com/Hahaha_ha2",
    # thêm web khác ở đây
]

INTERVAL = 5
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--mute-audio"]
        )

        pages = []

        for url in URLS:
            page = await browser.new_page()
            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                # đợi video load
                await asyncio.sleep(5)

                # ép video autoplay
                await page.add_init_script("""
                    document.querySelectorAll("video").forEach(v => {
                        v.muted = true;
                        v.play().catch(()=>{});
                    });
                """)

                pages.append(page)
                print("✔ Loaded:", url)

            except TimeoutError:
                print("❌ Timeout:", url)

        round_idx = 1
        while True:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"📸 Round {round_idx}")

            for i, page in enumerate(pages):
                try:
                    filename = f"{SAVE_DIR}/site{i+1}_round{round_idx}_{ts}.png"
                    await page.screenshot(path=filename)
                    print(" ✔", filename)
                except Exception as e:
                    print(" ❌ Screenshot error:", e)

            round_idx += 1
            await asyncio.sleep(INTERVAL)

asyncio.run(main())
