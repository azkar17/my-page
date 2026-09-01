from playwright.sync_api import sync_playwright
import time

URL = "https://azkar17.github.io/my-page/"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle", timeout=60000)
    time.sleep(4)  # let GitHub/GitLab stats settle
    # freeze typewriter/caret
    pg.evaluate("""() => {
        const el = document.getElementById('role');
        if (el) el.textContent = (window.CONFIG && CONFIG.role) || 'Laravel Developer';
        const caret = document.getElementById('role-caret');
        if (caret) caret.style.display = 'none';
    }""")
    time.sleep(1)
    pg.screenshot(path="snap_top.png", full_page=False)
    pg.screenshot(path="snap_full.png", full_page=True)
    print("OK title:", pg.title())
    b.close()
