import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.db.models import Base

# Импортируем модели, чтобы SQLAlchemy знала, что создавать
# (убедитесь, что Notification тоже есть в models.py, если вы его используете,
# но для создания таблиц events и registrations этого достаточно)
import app.db.models


async def fix_database():
    print("🔄 Исправление базы данных...")

    async with engine.begin() as conn:
        # 1. Отключаем проверку внешних ключей (на всякий случай, это "силовой" метод)
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        print("🗑️ Удаляем старые таблицы...")
        # Удаляем в правильном порядке (или принудительно)
        await conn.execute(text("DROP TABLE IF EXISTS registrations"))
        await conn.execute(text("DROP TABLE IF EXISTS notifications"))  # <--- Добавили это
        await conn.execute(text("DROP TABLE IF EXISTS events"))

        # Включаем проверку обратно
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        # 2. Создаем таблицы заново
        print("✨ Создаем новые таблицы...")
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Успешно! Таблицы пересозданы. Можно запускать бота.")


if __name__ == "__main__":
    asyncio.run(fix_database())