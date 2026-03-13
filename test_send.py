"""
Simple test to send a message directly using aiogram
"""
import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.DEBUG)

TOKEN = "8643690918:AAF2cclKGfyECczdoQv1hvgAQ1Ym-nOicsE"
OWNER_ID = 8337495954

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    
    print("Bot created, attempting to send message...")
    
    try:
        msg = await bot.send_message(OWNER_ID, "🧪 Test tin nhan truc tiep!")
        print(f"SUCCESS! Message sent with ID: {msg.message_id}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

