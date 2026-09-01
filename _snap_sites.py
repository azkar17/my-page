from playwright.sync_api import sync_playwright
import time

TARGETS = [
    ("https://liga.faselangor.my", "images/liga-fa.png"),
    ("https://order.speggit.my", "images/speggit-order.png"),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    for url, out in TARGETS:
        try:
            pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)  # let page settle / redirects
            pg.screenshot(path=out, full_page=False)
            print("OK", url, "->", out, "| title:", pg.title()[:60])
            pg.close()
        except Exception as e:
            print("FAIL", url, "->", str(e)[:120])
    b.close()
