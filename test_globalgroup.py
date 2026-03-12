import asyncio
import json
from aiogram import Bot
from config import TOKEN
from modules.global_ban import bot_groups

async def test():
    print("=== /globalgroup TEST ===")
    print(f"Groups loaded: {len(bot_groups)}")
    
    if not bot_groups:
        print("❌ bot_groups rỗng - add bot to groups first!")
        return
    
    text = "🧪 <b>TEST GLOBALGROUP từ BLACKBOXAI</b>\nHoạt động!"
    
    bot = Bot(token=TOKEN)
    sent = 0
    for gid in list(bot_groups):
        try:
            msg = await bot.send_message(gid, text, parse_mode="HTML")
            await bot.pin_chat_message(gid, msg.message_id)
            print(f"✅ Group {gid}: sent & pinned msg_id {msg.message_id}")
            sent += 1
        except Exception as e:
            print(f"❌ Group {gid}: {e}")
        await asyncio.sleep(0.1)
    
    print(f"COMPLETE: {sent}/{len(bot_groups)} success")
    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(test())
