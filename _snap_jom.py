from playwright.sync_api import sync_playwright
import os, time

CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe")

BASE = "http://jom-mancing.test"
EMAIL = os.environ.get("JOM_EMAIL", "penganjur@jommancing.test")   # seeded demo organiser (DemoSeeder)
PASSWORD = os.environ.get("JOM_PASSWORD", "password")

def shot(pg, url, path, wait=2.5):
    pg.goto(url, wait_until="networkidle", timeout=45000)
    time.sleep(wait)
    pg.screenshot(path=path, full_page=False)
    print("saved", path, "|", pg.title()[:60])

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, headless=True)
    ctx = b.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    pg = ctx.new_page()

    # 1 + 2 — public pages (BM, light)
    shot(pg, f"{BASE}/events", "images/jom-mancing-events.png")
    shot(pg, f"{BASE}/events/9/scoreboard", "images/jom-mancing-scoreboard.png")

    # log in as the demo organiser
    pg.goto(f"{BASE}/login", wait_until="networkidle", timeout=45000)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', PASSWORD)
    pg.click('button[type="submit"]')
    pg.wait_for_load_state("networkidle", timeout=45000)
    print("after login:", pg.url)

    # 3 — admin event list (BM, light)
    shot(pg, f"{BASE}/events", "images/jom-mancing-admin.png")

    # 4 — admin dashboard (EN, dark)
    pg.goto(f"{BASE}/locale/en", wait_until="networkidle", timeout=45000)
    pg.evaluate("localStorage.setItem('theme','dark')")
    shot(pg, f"{BASE}/dashboard", "images/jom-mancing-dashboard.png")

    # restore BM + light so the next run starts clean
    pg.evaluate("localStorage.setItem('theme','light')")
    pg.goto(f"{BASE}/locale/bm", wait_until="networkidle", timeout=45000)
    b.close()
