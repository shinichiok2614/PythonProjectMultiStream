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

    # 👉 Click xác nhận tuổi (nếu có)
    try:
        await page.wait_for_selector(
            config.AGE_CONFIRM_SELECTOR,
            timeout=5000
        )
        print("👉 Click age confirm")
        await page.click(config.AGE_CONFIRM_SELECTOR)
        await asyncio.sleep(2)
    except TimeoutError:
        pass

    return page


async def screenshot_with_fallback(page, output_path):
    """
    Ưu tiên chụp vùng video.
    Không có video → chụp toàn trang.
    """
    try:
        layer = await page.wait_for_selector(
            config.VIDEO_LAYER_SELECTOR,
            timeout=config.VIDEO_WAIT_TIMEOUT
        )

        # Ưu tiên screenshot element
        try:
            await layer.screenshot(path=output_path)
            print(" 🎥 Video captured")
            return
        except:
            pass

        # Fallback bounding box
        box = await layer.bounding_box()
        if box:
            await page.screenshot(
                path=output_path,
                clip={
                    "x": box["x"],
                    "y": box["y"],
                    "width": box["width"],
                    "height": box["height"]
                }
            )
            print(" 🎥 Video captured (clip)")
            return

        raise Exception("No bounding box")

    except Exception:
        # ❌ Không phát hiện video → chụp toàn trang
        print(" ⚠ Video not found → capture full page")
        await page.screenshot(path=output_path, full_page=False)


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

            # 🔄 ĐỌC LẠI DANH SÁCH LINK MỖI LƯỢT
            urls = list(dict.fromkeys(config.URLS))

            # ➕ THÊM LINK MỚI
            for url in urls:
                if url not in pages:
                    try:
                        page = await open_page(context, url)
                        pages[url] = page
                        print("➕ Added:", url)
                    except Exception as e:
                        print("❌ Open error:", url, e)

            # ❌ XÓA LINK ĐÃ BỎ
            for url in list(pages.keys()):
                if url not in urls:
                    await pages[url].close()
                    del pages[url]
                    print("➖ Removed:", url)

            # 📷 CHỤP 1 LƯỢT TOÀN BỘ
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            idx = 1

            for url, page in pages.items():
                try:
                    fname = f"{config.SAVE_DIR}/site{idx}_round{round_idx}_{ts}.png"
                    await screenshot_with_fallback(page, fname)
                    print(" ✔", fname)
                except Exception as e:
                    print(" ❌ Screenshot error:", url, e)
                idx += 1

            round_idx += 1
            await asyncio.sleep(config.INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
