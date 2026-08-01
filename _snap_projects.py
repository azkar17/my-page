from playwright.sync_api import sync_playwright
import os, time

os.makedirs("images", exist_ok=True)

# (slug, url) — try each; capture whatever renders
TARGETS = [
    ("noderight-dental", "https://noderightdental.com"),
    ("mapa",             "http://mapa.test"),
    ("speggit-order",    "https://order.speggit.my"),
    ("liga-fa",          "https://liga.faselangor.com"),
    ("tim-katang",       "https://timkatangempire.com"),
]

results = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for slug, url in TARGETS:
        pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        status = "?"
        try:
            resp = pg.goto(url, wait_until="networkidle", timeout=25000)
            status = resp.status if resp else "no-resp"
            time.sleep(2)
            out = f"images/{slug}.png"
            pg.screenshot(path=out, full_page=False)  # viewport only = thumbnail-friendly
            sz = os.path.getsize(out)
            results.append((slug, url, status, out, sz, pg.title()))
        except Exception as e:
            results.append((slug, url, status, None, 0, f"ERR: {str(e)[:80]}"))
        pg.close()
    b.close()

for slug, url, status, out, sz, note in results:
    print(f"{slug:18} {str(status):8} {str(sz):>8}B  {note[:60]}")
