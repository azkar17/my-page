from playwright.sync_api import sync_playwright
import time

URL = "https://azkar17.github.io/my-page/"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle", timeout=60000)
    time.sleep(4)
    pg.evaluate("""() => {
        const el = document.getElementById('role');
        if (el) el.textContent = (window.CONFIG && CONFIG.role) || 'Laravel Developer';
        const caret = document.getElementById('role-caret');
        if (caret) caret.style.display = 'none';
    }""")
    time.sleep(1)
    # scroll to projects section and capture it
    el = pg.query_selector("#proj-section")
    if el:
        el.scroll_into_view_if_needed()
        time.sleep(1)
        el.screenshot(path="snap_projects.png")
        print("projects section captured")
    # also capture first project card area with links
    links = pg.evaluate("""() => {
        const els = document.querySelectorAll('.p-link');
        return Array.from(els).map(e => e.textContent.trim());
    }""")
    print("link chips found:", links)
    b.close()
