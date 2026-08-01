"""Capture local .test sites into images/<slug>.png at the card's 16:10 aspect.

Usage:  python _capture.py <host> <slug> [<host> <slug> ...]
Example: python _capture.py trello-strutt.test trello-strutt
"""
import sys, time
from playwright.sync_api import sync_playwright
from PIL import Image

W, H = 1440, 900          # 16:10 — matches .proj-shot aspect-ratio
OUT_W = 1280              # final width; keeps files ~300KB like the existing images


def shrink(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((OUT_W, OUT_W), Image.LANCZOS)
    im.quantize(colors=256, method=Image.MEDIANCUT,
                dither=Image.FLOYDSTEINBERG).save(path, "PNG", optimize=True)
    return im.size


def main(pairs):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for host, slug in pairs:
            path = f"images/{slug}.png"
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1.5)
            try:
                pg.goto(f"http://{host}/", wait_until="networkidle", timeout=45000)
                time.sleep(2.5)
                pg.screenshot(path=path)
                size = shrink(path)
                print(f"  OK   {slug:<18} {host:<22} {size[0]}x{size[1]}  '{pg.title()[:45]}'")
            except Exception as e:
                print(f"  FAIL {slug:<18} {host:<22} {type(e).__name__}: {str(e)[:70]}")
            finally:
                pg.close()
        b.close()


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or len(a) % 2:
        sys.exit(__doc__)
    main(list(zip(a[::2], a[1::2])))
