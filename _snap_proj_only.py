from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    pg.goto("http://127.0.0.1:8777/index.html", wait_until="networkidle", timeout=60000)
    time.sleep(2)
    el = pg.query_selector("#proj-section")
    el.scroll_into_view_if_needed()
    time.sleep(0.5)
    el.screenshot(path="snap_projects.png")
    print("OK")
    b.close()
