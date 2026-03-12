import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Update, Message
from config import TOKEN
from modules import admin, locks, schedule, global_ban

# Gán bot_groups từ global_ban để tránh circular import
admin.bot_groups = global_ban.bot_groups

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Kiểm tra có chạy trên Railway không
IS_RAILWAY = "RAILWAY_PUBLIC_DOMAIN" in os.environ
RAILWAY_PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        logger.info(f"MIDDLEWARE HANDLER={handler.__name__} event={type(event).__name__} chat_id={getattr(event, 'chat', None).id if hasattr(event, 'chat') else 'N/A'} user_id={getattr(event, 'from_user', None).id if hasattr(event, 'from_user') else 'N/A'} text={getattr(event, 'text', 'N/A')[:50]}")
        try:
            result = await handler(event, data)
            logger.info(f"MIDDLEWARE SUCCESS {handler.__name__}")
            return result
        except Exception as e:
            logger.error(f"MIDDLEWARE ERROR {handler.__name__}: {e}")
            raise

dp.message.middleware(LoggingMiddleware())

# Test handler - NO FILTER
@dp.message(Command("test"))
async def test_cmd(message: Message):
    logger.info(f"TEST CMD chat={message.chat.id} user={message.from_user.id}")
    try:
        await message.answer("🧪 TEST OK - Bot works!")
        logger.info(f"TEST OK chat={message.chat.id}")
    except Exception as e:
        logger.error(f"TEST ERROR chat={message.chat.id}: {e}")

# Include routers AFTER test
dp.include_router(locks.router)
dp.include_router(schedule.router)
dp.include_router(global_ban.router)
dp.include_router(admin.router)

# Log all routers
logger.info(f"Locks router: {locks.router}")
logger.info(f"Schedule router: {schedule.router}")
logger.info(f"Global ban router: {global_ban.router}")
logger.info(f"Admin router: {admin.router}")


# ================= STARTUP =================

async def on_startup():
    if IS_RAILWAY and RAILWAY_PUBLIC_URL:
        await bot.delete_webhook(drop_pending_updates=True)

        webhook_url = f"https://{RAILWAY_PUBLIC_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook set to: {webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Running in polling mode (local)")


async def on_shutdown():
    if IS_RAILWAY:
        await bot.delete_webhook()
        logging.info("Webhook deleted")


# ================= WEBHOOK =================

async def handle_webhook(request):
    try:
        update_data = await request.json()
        logger.info(f"WEBHOOK NHẬN: {update_data}")
        
        update = Update(**update_data)
        
        # Log chat type để debug
        if update.message:
            logger.info(f"Chat Type: {update.message.chat.type} | Chat ID: {update.message.chat.id}")
        
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
    # Xóa webhook nếu còn
    await bot.delete_webhook(drop_pending_updates=True)

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
