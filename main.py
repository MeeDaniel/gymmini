import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from src.core.config import settings
from src.bot.handlers import router as bot_router
from src.api.main import app as api_app

logging.basicConfig(level=logging.INFO)

async def run_bot():
    if settings.bot_token == "placeholder_token":
        logging.warning("BOT_TOKEN is not set. Bot will not start.")
        return
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(bot_router)
    await dp.start_polling(bot)

async def main():
    bot_task = asyncio.create_task(run_bot())
    
    config = uvicorn.Config(api_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    api_task = asyncio.create_task(server.serve())
    
    await asyncio.gather(bot_task, api_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down")
