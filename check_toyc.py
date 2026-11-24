import json
import os
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.toyc.com.hk/products"
PARAMS = {"query": "plakoro"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
}
SEEN_FILE = "seen_toyc.json"

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "").strip()


def load_seen() -> list[str]:
    if not os.path.exists(SEEN_FILE):
        return []
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_seen(items: list[str]) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def fetch_toyc_products() -> list[tuple[str, str]]:
    resp = requests.get(SEARCH_URL, headers=HEADERS, params=PARAMS, timeout=20)
    print("TOYC Status:", resp.status_code)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    seen_urls = set()
    products = []

    for a in soup.select("a[href*='/products/']"):
        raw_href = (a.get("href") or "").strip()
        if not raw_href:
            continue
        clean_url = raw_href.split("?")[0]
        if clean_url.startswith("/"):
            clean_url = f"https://www.toyc.com.hk{clean_url}"
        if "/products/" not in clean_url or clean_url in seen_urls:
            continue

        seen_urls.add(clean_url)
        title = a.get_text(" ", strip=True)
        if not title:
            title = clean_url.rstrip("/").split("/")[-1]
        products.append((title, clean_url))

    return products


def send_telegram(text: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[Preview only - no TG secrets set]\n" + text)
        return

    api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    resp = requests.post(api_url, json=payload, timeout=15)
    print("TG Status:", resp.status_code)
    resp.raise_for_status()


def main() -> None:
    seen_list = load_seen()
    seen_set = set(seen_list)

    products = fetch_toyc_products()
    print(f"Found {len(products)} unique TOYC product URLs.")

    new_items = []
    for title, url in products:
        if url not in seen_set:
            new_items.append((title, url))
            seen_list.append(url)
            seen_set.add(url)

    print(f"New TOYC items: {len(new_items)}")
    for title, url in new_items:
        msg = f"🆕 TOYC 新 PLAKORO 項目\n📦 {title}\n🔗 {url}"
        send_telegram(msg)

    if new_items:
        save_seen(seen_list)


if __name__ == "__main__":
    main()
