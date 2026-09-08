"""Capture Solar Referral screens into images/solar-referral-*.png.

Local Laragon site (http://solar-referal.test) with the seeded demo member.
Credentials come from SR_EMAIL / SR_PASSWORD, defaulting to the test account.
"""
import os, time
from playwright.sync_api import sync_playwright
from PIL import Image

OUT_W = 1280          # final width — keeps files in line with the other project images

CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe")
if not os.path.exists(CHROME):
    CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe")

BASE = "http://solar-referal.test"
EMAIL = os.environ.get("SR_EMAIL", "azkar@test.com")
PASSWORD = os.environ.get("SR_PASSWORD", "password")

def shot(pg, url, path, wait=2.5, full=False):
    pg.goto(url, wait_until="networkidle", timeout=45000)
    time.sleep(wait)
    pg.screenshot(path=path, full_page=full)
    im = Image.open(path).convert("RGB")
    im.thumbnail((OUT_W, OUT_W), Image.LANCZOS)
    im.save(path, "PNG", optimize=True)
    print(f"saved {path} {im.size[0]}x{im.size[1]} | {pg.title()[:60]}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()

    pg.goto(f"{BASE}/login", wait_until="networkidle", timeout=45000)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', PASSWORD)
    pg.click('button[type="submit"]')
    pg.wait_for_load_state("networkidle", timeout=45000)
    print("after login:", pg.url)
    if "login" in pg.url:
        raise SystemExit("login failed — check SR_EMAIL / SR_PASSWORD")

    shot(pg, f"{BASE}/dashboard", "images/solar-referral-dashboard.png")
    shot(pg, f"{BASE}/dashboard/earnings", "images/solar-referral-earnings.png")
    b.close()
