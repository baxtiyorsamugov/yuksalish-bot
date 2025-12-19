from pathlib import Path
from dotenv import dotenv_values

# Корень проекта (на уровень выше папки app)
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env строго из корня проекта
env = dotenv_values(BASE_DIR / ".env")

# Обязательные переменные
BOT_TOKEN = env.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

DB_DSN = env.get("DB_DSN")
if not DB_DSN:
    raise RuntimeError("DB_DSN not found in .env")

# Опциональные
ADMIN_TG_IDS = {
    int(x.strip())
    for x in (env.get("ADMIN_TG_IDS") or "").split(",")
    if x.strip().isdigit()
}

BASE_URL = env.get("BASE_URL", "")
