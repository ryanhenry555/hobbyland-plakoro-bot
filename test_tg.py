import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8")

API_URL = "https://backend.hobbylandeshop.com/api/products"
STATE_FILE = "seen_skus.json"

TG_BOT_TOKEN = os.environ.get("9281972053:AAFjX4xCq-lImPAvdh-l354KtI3E4p5BUz8", "").strip()
TG_CHAT_ID = os.environ.get("407555417", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.hobbylandshop.com",
    "Referer": "https://www.hobbylandshop.com/",
}

PAYLOAD = {
    "page": 1,
    "search": "plakoro",
}


def load_seen() -> list[str]:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    return []


def save_seen(seen_list: list[str]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_list, f, ensure_ascii=False, indent=2)


def send_telegram(message: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[未設定 TG Secrets，改為印出訊息]\n" + message)
        return

    tg_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        tg_url,
        data={
            "chat_id": TG_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=15,
    )
    resp.raise_for_status()


def main() -> None:
    resp = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=15)
    print("Status:", resp.status_code)
    resp.raise_for_status()

    payload_data = resp.json()
    items = payload_data.get("data", {}).get("list", [])

    seen_list = load_seen()
    seen_set = set(seen_list)
    new_items = []

    for item in items:
        sku = str(item.get("sku") or "").strip()
        title = str(item.get("title") or "").strip()
        price = item.get("price")
        sell_type = item.get("sell_type")
        link = str(item.get("link") or "").strip()
        full_link = link if link.startswith("http") else f"https://www.hobbylandshop.com{link}"

        if sku and sku not in seen_set:
            seen_set.add(sku)
            seen_list.append(sku)
            new_items.append((sku, title, price, sell_type, full_link))

    print(f"今次搵到：{len(items)} 件 | 新增未見過：{len(new_items)} 件")

    for sku, title, price, sell_type, full_link in new_items:
        msg = (
            "🎲 Hobby Land 發現新 PLAKORO 預訂/商品！\n"
            f"編號：{sku}\n"
            f"名稱：{title}\n"
            f"價錢：${price}\n"
            f"類型：{sell_type}\n"
            f"連結：{full_link}"
        )
        send_telegram(msg)

    if new_items:
        save_seen(seen_list)


if __name__ == "__main__":
    main()