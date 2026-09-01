from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
    pg.goto("https://order.speggit.my", wait_until="domcontentloaded", timeout=45000)
    # wait for Cloudflare challenge to auto-solve (up to 30s)
    for i in range(15):
        time.sleep(2)
        title = pg.title()
        if "Just a moment" not in title and "security" not in title.lower():
            break
    time.sleep(3)
    pg.screenshot(path="images/speggit-order.png", full_page=False)
    print("title:", pg.title()[:80])
    b.close()
