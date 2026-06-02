"""
Персональные поздравления близким людям через Telegram (Telethon).

Где взять api_id и api_hash:
  1. Открой https://my.telegram.org и войди под своим номером телефона.
  2. Перейди в раздел "API development tools".
  3. Создай приложение (название/short name любое, платформа — Desktop).
  4. Скопируй api_id (число) и api_hash (строка) в файл .env рядом со скриптом
     или подставь их в переменные ниже.

Установка зависимостей:
    pip install telethon python-dotenv

Запуск:
    python send_greetings.py

Логика:
  - Получатели читаются только из recipients.csv (никакого автоперебора контактов).
  - Шаблон сообщения берётся из template.txt (плейсхолдеры {name}, {occasion}).
  - Между сообщениями — случайная пауза 5..15 секунд.
  - Все результаты пишутся в send_log.txt.
"""

import asyncio
import csv
import os
import random
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    UserPrivacyRestrictedError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
RECIPIENTS_FILE = BASE_DIR / "recipients.csv"
TEMPLATE_FILE = BASE_DIR / "template.txt"
LOG_FILE = BASE_DIR / "send_log.txt"
SESSION_NAME = "greetings_session"

API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")

MIN_DELAY_SEC = 5
MAX_DELAY_SEC = 15


def log(line: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{stamp}] {line}"
    print(entry)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


def load_recipients() -> list[dict]:
    """
    Читает recipients.csv. Колонки:
      contact  — @username, телефон в формате +79991234567 или числовой user_id
      name     — имя для подстановки в шаблон
      occasion — повод (например "день рождения", "Новый год")
    """
    if not RECIPIENTS_FILE.exists():
        log(f"Файл {RECIPIENTS_FILE.name} не найден — отправлять некому.")
        return []

    recipients: list[dict] = []
    with RECIPIENTS_FILE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contact = (row.get("contact") or "").strip()
            name = (row.get("name") or "").strip()
            occasion = (row.get("occasion") or "").strip()
            if not contact:
                continue
            recipients.append({"contact": contact, "name": name, "occasion": occasion})
    return recipients


def load_template() -> str:
    if not TEMPLATE_FILE.exists():
        # Минимальная заглушка, чтобы скрипт работал и без template.txt.
        return "Привет, {name}! Поздравляю с {occasion}!"
    return TEMPLATE_FILE.read_text(encoding="utf-8").strip()


def resolve_entity_arg(contact: str):
    """Превращает строку из CSV в то, что Telethon примет в client.get_entity()."""
    if contact.lstrip("-").isdigit():
        return int(contact)
    return contact  # @username или +телефон


async def send_all() -> None:
    if not API_ID or not API_HASH:
        log("Не заданы TG_API_ID / TG_API_HASH — прерываю запуск.")
        return

    recipients = load_recipients()
    if not recipients:
        log("Список получателей пуст — ничего не отправляю.")
        return

    template = load_template()
    log(f"К отправке: {len(recipients)} получателей.")

    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        for i, r in enumerate(recipients, 1):
            contact = r["contact"]
            try:
                entity = await client.get_entity(resolve_entity_arg(contact))
                text = template.format(name=r["name"] or "друг", occasion=r["occasion"] or "праздник")
                await client.send_message(entity, text)
                log(f"OK  [{i}/{len(recipients)}] {contact} ({r['name']})")
            except (UsernameNotOccupiedError, UsernameInvalidError):
                log(f"FAIL [{i}/{len(recipients)}] {contact}: такого username нет.")
            except UserPrivacyRestrictedError:
                log(f"FAIL [{i}/{len(recipients)}] {contact}: настройки приватности запрещают писать.")
            except PeerFloodError:
                log(f"STOP {contact}: Telegram пометил аккаунт как спамящий. Останавливаюсь.")
                break
            except FloodWaitError as e:
                log(f"WAIT {contact}: Telegram просит подождать {e.seconds} сек. Сплю.")
                await asyncio.sleep(e.seconds + 1)
                continue
            except Exception as e:
                log(f"FAIL [{i}/{len(recipients)}] {contact}: {type(e).__name__}: {e}")

            if i < len(recipients):
                delay = random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC)
                await asyncio.sleep(delay)

    log("Готово.")


if __name__ == "__main__":
    asyncio.run(send_all())
