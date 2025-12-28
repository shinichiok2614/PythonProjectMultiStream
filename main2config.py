import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
import config

# ================== UTILS ==================
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


async def open_page(context, url):
    page = await context.new_page()
    await page.set_viewport_size({
        "width": config.VIEWPORT_WIDTH,
        "height": config.VIEWPORT_HEIGHT
    })

    await page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # 👉 click xác nhận tuổi (nếu có)
    try:
        await page.wait_for_selector(
            config.AGE_CONFIRM_SELECTOR,
            timeout=5000
        )
        await page.click(config.AGE_CONFIRM_SELECTOR)
        await asyncio.sleep(2)
    except TimeoutError:
        pass

    return page


# ================== MAIN ==================
async def main():
    ensure_dir(config.SAVE_DIR)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            config.PROFILE_DIR,
            headless=True,
            args=["--mute-audio"]
        )

        pages = {}  # url -> page
        round_idx = 1

        while True:
            print(f"\n📸 ROUND {round_idx}")

            # 🔄 LOAD CONFIG MỚI MỖI LƯỢT
            urls = list(dict.fromkeys(config.URLS))  # bỏ trùng

            # ➕ ADD LINK MỚI
            for url in urls:
                if url not in pages:
                    try:
                        page = await open_page(context, url)
                        pages[url] = page
                        print("➕ Added:", url)
                    except Exception as e:
                        print("❌ Open error:", url, e)

            # ❌ REMOVE LINK ĐÃ BỊ XÓA
            for url in list(pages.keys()):
                if url not in urls:
                    await pages[url].close()
                    del pages[url]
                    print("➖ Removed:", url)

            # 📷 CHỤP 1 LƯỢT TOÀN BỘ
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, (url, page) in enumerate(pages.items(), start=1):
                try:
                    fname = f"{config.SAVE_DIR}/site{i}_round{round_idx}_{ts}.png"
                    await page.screenshot(path=fname)
                    print(" ✔", fname)
                except Exception as e:
                    print(" ❌ Screenshot error:", url, e)

            round_idx += 1
            await asyncio.sleep(config.INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
