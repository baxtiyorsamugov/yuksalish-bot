from pathlib import Path
from dotenv import dotenv_values

# Корень проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env
env = dotenv_values(BASE_DIR / ".env")

# Обязательные переменные
BOT_TOKEN = env.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

DB_DSN = env.get("DB_DSN")
if not DB_DSN:
    raise RuntimeError("DB_DSN not found in .env")

# === ИСПРАВЛЕНИЕ ЗДЕСЬ ===
# Переименовали ADMIN_TG_IDS -> ADMIN_IDS
raw_admins = env.get("ADMIN_TG_IDS") or ""

ADMIN_IDS = [
    int(x.strip())
    for x in raw_admins.split(",")
    if x.strip().isdigit()
]
# ========================

BASE_URL = env.get("BASE_URL", "")