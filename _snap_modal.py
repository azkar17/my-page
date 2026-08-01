from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    pg.goto("http://127.0.0.1:8777/index.html", wait_until="networkidle", timeout=60000)
    time.sleep(2)

    # 1) Trello-Strutt (last card) — placeholder gallery + rich stack
    cards = pg.query_selector_all(".proj-card")
    print("cards:", len(cards))
    cards[-1].click()
    time.sleep(0.6)
    pg.screenshot(path="snap_modal_trello.png", full_page=False)
    # verify content
    print("title:", pg.text_content("#m-title"))
    print("stack visible:", pg.is_visible("#m-stack-wrap"))
    print("stack tags:", pg.eval_on_selector_all("#m-stack .tag", "els => els.map(e=>e.textContent)"))
    # close via Escape
    pg.keyboard.press("Escape")
    time.sleep(0.4)
    print("closed:", not pg.is_visible("#proj-modal"))

    # 2) Noderight Dental (first card) — real screenshot gallery
    cards[0].click()
    time.sleep(0.8)
    pg.screenshot(path="snap_modal_noderight.png", full_page=False)
    print("title2:", pg.text_content("#m-title"))
    b.close()
