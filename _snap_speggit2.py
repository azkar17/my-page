from playwright.sync_api import sync_playwright
import time, os

CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe")
if not os.path.exists(CHROME):
    CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, headless=True, args=[
        "--disable-blink-features=AutomationControlled",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    ])
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto("https://order.speggit.my", wait_until="domcontentloaded", timeout=45000)
    for i in range(20):
        time.sleep(2)
        title = pg.title()
        if "Just a moment" not in title:
            break
    time.sleep(3)
    pg.screenshot(path="images/speggit-order.png", full_page=False)
    print("title:", pg.title()[:80])
    b.close()
