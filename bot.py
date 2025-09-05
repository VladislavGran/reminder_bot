import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router
from db import init_db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
