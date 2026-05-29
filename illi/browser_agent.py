from playwright.sync_api import sync_playwright
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / 'logs' / 'screenshots'
OUT.mkdir(parents=True, exist_ok=True)


def start_browser(profile_dir: str = None, headless: bool = False):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return p, browser, context, page


def snapshot_page(page, name_prefix='snapshot'):
    ts = int(time.time())
    path = OUT / f"{name_prefix}_{ts}.png"
    page.screenshot(path=str(path))
    md = OUT / f"{name_prefix}_{ts}.md"
    md.write_text(f"![{name_prefix}]({path.name})\n\nCaptured: {ts}")
    return str(path)


def monitor_whatsapp(page, contact_name: str, callback=None, poll=3):
    # Requires user to login to web.whatsapp.com in the opened context
    # This is a best-effort helper that looks for contact message nodes.
    try:
        while True:
            # basic selector for chat list items
            chats = page.query_selector_all('div[role="row"]')
            for c in chats:
                title = c.inner_text().lower()
                if contact_name.lower() in title:
                    c.click()
                    time.sleep(1)
                    messages = page.query_selector_all('div.message-in, div.message-out')
                    last = messages[-1].inner_text() if messages else ''
                    if callback:
                        callback(last)
            time.sleep(poll)
    except Exception:
        return

