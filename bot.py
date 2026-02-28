import asyncio
import logging
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from config import TOKEN
from modules import admin, locks, schedule

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(locks.router)
dp.include_router(schedule.router)
dp.include_router(admin.router)

# Kiểm tra xem có đang chạy trên Railway không
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None
RAILWAY_PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_URL")

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Chạy khi bot khởi động"""
    if IS_RAILWAY and RAILWAY_PUBLIC_URL:
        await bot.set_webhook(f"{RAILWAY_PUBLIC_URL}/webhook")
        logging.info(f"Webhook set to: {RAILWAY_PUBLIC_URL}/webhook")
    else:
        logging.info("Running in polling mode (local)")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Chạy khi bot tắt"""
    if IS_RAILWAY:
        await bot.delete_webhook()
        logging.info("Webhook deleted")

async def handle_webhook(request):
    """Xử lý webhook request"""
    try:
        update_data = await request.json()
        update = Update(**update_data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return web.Response(text="Error", status=500)

async def start_polling():
    """Chạy bot với polling (cho local)"""
    try:
        schedule.start_scheduler()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")
    
    await asyncio.sleep(1)
    await dp.start_polling(bot, drop_pending_updates=True)

async def start_webhook():
    """Chạy bot với webhook (cho Railway)"""
    try:
        schedule.start_scheduler()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")
    
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    
    # Cấu hình webhook
    await on_startup(dp, bot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    
    logging.info("Webhook server started on port 8080")
    
    # Giữ bot chạy
    try:
        await asyncio.Event().wait()
    finally:
        await on_shutdown(dp, bot)

async def main():
    if IS_RAILWAY:
        await start_webhook()
    else:
        await start_polling()

if __name__ == "__main__":
    asyncio.run(main())
