import asyncio
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN
# from config import BOT_TOKEN
from app.bot.handlers import start, registration, admin, about, events



async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(about.router)
    dp.include_router(events.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
