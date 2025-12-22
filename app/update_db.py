import asyncio
from app.db.session import engine
from app.db.models import Base


async def create_missing_tables():
    print("⏳ Проверяем и создаем недостающие таблицы...")

    async with engine.begin() as conn:
        # Эта функция создаст ТОЛЬКО те таблицы, которых еще нет.
        # Старые таблицы (users, profiles) она не тронет и данные НЕ удалит.
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Готово! Таблицы events и registrations созданы.")


if __name__ == "__main__":
    asyncio.run(create_missing_tables())