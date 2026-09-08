"""Capture Trello-Strutt screens into images/trello-strutt-*.png.

Customer names and plate numbers are replaced in the DOM before each shot —
this is a public portfolio page, so no real workshop customer data ships.

Login pages need TS_EMAIL / TS_PASSWORD in the environment; without them only
the public guest board is captured.
"""
import os, time
from playwright.sync_api import sync_playwright
from PIL import Image

OUT_W = 1280          # final width — keeps files in line with the other project images

CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe")
if not os.path.exists(CHROME):
    CHROME = os.path.expanduser("~/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe")

BASE = "http://trello-strutt.test"
EMAIL, PASSWORD = os.environ.get("TS_EMAIL"), os.environ.get("TS_PASSWORD")

ANON = r"""
() => {
  const FIRST = ["AHMAD FAIZAL","SITI NURHALIZA","MUHAMMAD IRFAN","NURUL AISYAH","DANIEL TAN",
                 "LEE WEI MING","ZARINA HALIM","RAJESH KUMAR","FARID RAZAK","MEI LING CHONG",
                 "HAKIM ISMAIL","PRIYA MENON"];
  const STAFF = ["Amir","Syafiq","Ravi","Hafiz","Jason","Nazrul","Wei Jie","Danish"];
  const PRE = ["WXA","JQB","BMT","VGK","PNC","WYR","MAA","KBL"];
  const hash = s => { let x = 7; for (let i = 0; i < s.length; i++) x = (x * 31 + s.charCodeAt(i)) >>> 0; return x; };
  const fakeName  = s => FIRST[hash(s) % FIRST.length];
  const fakeStaff = s => STAFF[hash(s) % STAFF.length];
  const fakePlate = s => PRE[hash(s) % PRE.length] + " " + (1000 + (hash(s) >>> 3) % 8999);
  const rx = /^(\s*)([^()]*?)\s*\(([^()]+)\)(.*)$/s;
  let hit = 0;

  // 1 - card titles: "CUSTOMER (MODEL - PLATE[ - JOB TYPE])"
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = []; while (w.nextNode()) nodes.push(w.currentNode);
  for (const node of nodes) {
    const t = node.nodeValue;
    if (!t || t.indexOf("(") < 0 || t.indexOf("-") < 0) continue;
    const m = t.match(rx); if (!m) continue;
    const parts = m[3].split(" - ");
    if (parts.length < 2 || !/\d/.test(parts[1])) continue;   // parts[1] is the plate slot
    parts[1] = fakePlate(parts[1]);
    const name = m[2].trim();
    node.nodeValue = m[1] + (name ? fakeName(name) + " " : "") + "(" + parts.join(" - ") + ")" + m[4];
    hit++;
  }

  // 2 - staff / technician names
  document.querySelectorAll(".member-name, .pending-card small, .card-member, .assignee").forEach(el => {
    const t = el.textContent.trim();
    if (!t || t === "-") return;
    el.textContent = fakeStaff(t);
    hit++;
  });

  return hit;
}
"""

def shot(pg, url, path, wait=2.5, full=False):
    pg.goto(url, wait_until="networkidle", timeout=45000)
    time.sleep(wait)
    n = pg.evaluate(ANON)
    time.sleep(0.3)
    pg.screenshot(path=path, full_page=full)
    im = Image.open(path).convert("RGB")
    im.thumbnail((OUT_W, OUT_W), Image.LANCZOS)
    im.save(path, "PNG", optimize=True)
    print(f"saved {path} {im.size[0]}x{im.size[1]} | anonymised {n} labels | {pg.title()[:50]}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()

    # public boards — no auth
    shot(pg, f"{BASE}/guest/time-tracking", "images/trello-strutt-live.png", wait=3.5)
    shot(pg, f"{BASE}/guest/time-checking", "images/trello-strutt.png", wait=3.5)   # cover shot

    if EMAIL and PASSWORD:
        pg.goto(f"{BASE}/login", wait_until="networkidle", timeout=45000)
        pg.fill('input[name="email"]', EMAIL)
        pg.fill('input[name="password"]', PASSWORD)
        pg.click('button[type="submit"]')
        pg.wait_for_load_state("networkidle", timeout=45000)
        print("after login:", pg.url)
        if "login" in pg.url:
            raise SystemExit("login failed — check TS_EMAIL / TS_PASSWORD")
        shot(pg, f"{BASE}/dashboard", "images/trello-strutt-dashboard.png")
        shot(pg, f"{BASE}/card", "images/trello-strutt-cards.png")
    else:
        print("TS_EMAIL / TS_PASSWORD not set — skipped dashboard + cards")
    b.close()
