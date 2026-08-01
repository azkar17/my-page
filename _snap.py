from playwright.sync_api import sync_playwright
import time

URL = "http://127.0.0.1:8777/index.html"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle", timeout=60000)
    time.sleep(3)  # let stats settle
    # freeze the typewriter on the full primary role for a clean capture
    pg.evaluate("""() => {
        const el = document.getElementById('role');
        const caret = document.getElementById('role-caret');
        if (el) el.textContent = (window.CONFIG && CONFIG.role) || 'Laravel Developer';
        if (caret) caret.style.display = 'none';
    }""")
    time.sleep(0.5)
    pg.screenshot(path="snap_full.png", full_page=True)
    pg.screenshot(path="snap_top.png", full_page=False)
    print("OK title:", pg.title())
    b.close()
