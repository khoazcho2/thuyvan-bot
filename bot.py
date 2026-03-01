import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update

from config import TOKEN
from modules import admin, locks, schedule

logging.basicConfig(level=logging.INFO)

# Kiểm tra có chạy trên Railway không
IS_RAILWAY = "RAILWAY_PUBLIC_DOMAIN" in os.environ
RAILWAY_PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Include router (thứ tự đúng)
dp.include_router(locks.router)
dp.include_router(schedule.router)
dp.include_router(admin.router)


# ================= STARTUP =================

async def on_startup():
    if IS_RAILWAY and RAILWAY_PUBLIC_URL:
        webhook_url = f"https://{RAILWAY_PUBLIC_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")
    else:
        logging.info("Running in polling mode (local)")


async def on_shutdown():
    if IS_RAILWAY:
        await bot.delete_webhook()
        logging.info("Webhook deleted")


# ================= WEBHOOK =================

async def handle_webhook(request):
    try:
        update_data = await request.json()
        update = Update(**update_data)
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return web.Response(text="Error", status=500)


async def start_webhook():
    await on_startup()

    try:
        schedule.start_scheduler()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"Webhook server started on port {PORT}")

    try:
        await asyncio.Event().wait()
    finally:
        await on_shutdown()


# ================= POLLING =================

async def start_polling():
    await on_startup()

    try:
        schedule.start_scheduler()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")

    await asyncio.sleep(1)
    await dp.start_polling(bot, drop_pending_updates=True)


# ================= MAIN =================

async def main():
    if IS_RAILWAY:
        await start_webhook()
    else:
        await start_polling()


if __name__ == "__main__":
    asyncio.run(main())
