import os
import json
import hashlib
import time
import re
import requests
from datetime import datetime, timedelta

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT = os.getenv("TG_CHAT_ID")
SEEN_FILE = "seen_ids.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen_set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_set), f, ensure_ascii=False)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            print(f"Ошибка Telegram: {resp.text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def fetch_projects():
    url = "https://zakupki.gov.ru/epz/order/quicksearch/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html, */*",
        "Referer": "https://zakupki.gov.ru/"
    }
    params = {
        "morph": "true",
        "searchString": "концепция OR изыскания OR ТЭО OR предпроект",
        "okpd2": "71100000,71121000,71122000",
        "pageNumber": 1,
        "pageSize": 50,
        "sortDirection": "DESC",
        "sortBy": "PUBLISH_DATE"
    }

    data = None
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 429:
                print(f"Лимит. Ждём 10 сек... (попытка {attempt+1})")
                time.sleep(10)
                continue
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "")
            if "json" in ct:
                data = resp.json()
            else:
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', resp.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
            if 
                break
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            time.sleep(5)

    if not data:
        print("Не удалось получить данные с ЕИС")
        return []

    items = data.get("data", []) or data.get("orderList", {}).get("orders", [])
    if not items:
        print("Объектов не найдено.")
        return []

    today = datetime.now()
    horizon = today + timedelta(days=1095)
    projects = []

    for item in items:
        date_str = (item.get("publishDate") or item.get("regDate") or "")[:10]
        try:
            if date_str and datetime.strptime(date_str, "%Y-%m-%d") > horizon:
                continue
        except:
            pass

        raw_id = f"{item.get('regNumber', '')}_{item.get('purchaseName', '')}"
        pid = hashlib.md5(raw_id.encode()).hexdigest()[:12]
        price = item.get("maxPrice")
        budget = f"{price:,.0f} руб." if price else "н/д"

        projects.append({
            "id": pid,
            "name": item.get("purchaseName", "Без названия"),
            "date": date_str or "н/д",
            "budget": budget,
            "customer": item.get("customerName", "н/д"),
            "investor": "н/д",
            "designer": "н/д",
            "contractor": "н/д"
        })

    print(f"Найдено {len(projects)} записей")
    return projects

def main():
    if not TG_TOKEN or not TG_CHAT:
        print("Не заданы TG_BOT_TOKEN или TG_CHAT_ID")
        return

    print("Запуск радара...")
    projects = fetch_projects()
    seen = load_seen()
    new = [p for p in projects if p["id"] not in seen]
    
    if not new:
        print("Новых объектов нет.")
        return

    seen.update(p["id"] for p in new)
    save_seen(seen)

    msg = "📡 <b>Радар: новые объекты РФ</b>\n\n"
    for p in new:
        msg += f"🏗️ <b>{p['name']}</b>\n"
        msg += f"📅 Дата: {p['date']}\n"
        msg += f"💰 Бюджет: {p['budget']}\n"
        msg += f"👥 Заказчик: {p['customer']}\n"
        msg += "────────────────────\n"

    send_to_telegram(msg)
    print(f"Отправлено {len(new)} объектов.")

if __name__ == "__main__":
    main()
