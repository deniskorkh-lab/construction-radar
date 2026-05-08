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
    """
    ТЕСТОВЫЕ ДАННЫЕ - для проверки работы бота
    """
    print("📦 Используем тестовые данные...")
    
    today = datetime.now()
    
    # Создаём 2 тестовых объекта
    projects = [
        {
            "id": "test_objekt_1",
            "name": "Разработка концепции развития парка «Зелёная роща»",
            "date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "budget": "45 000 000 руб.",
            "customer": "Администрация г. Казани",
            "investor": "Муниципальный бюджет",
            "designer": "Не определён",
            "contractor": "Не определён"
        },
        {
            "id": "test_objekt_2",
            "name": "Инженерные изыскания для строительства моста через реку",
            "date": (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            "budget": "120 000 000 руб.",
            "customer": "ФКУ «Росавтодор»",
            "investor": "Федеральный бюджет",
            "designer": "ФГУП «ГИДРОПРОЕКТ»",
            "contractor": "Тендер не объявлен"
        }
    ]
    
    print(f"✅ Сгенерировано {len(projects)} тестовых объекта")
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
