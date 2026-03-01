from aiogram import Router, types, Bot
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = Router()
scheduler = AsyncIOScheduler()
group_jobs = {}
group_last_message = {}

async def is_admin(message: types.Message):
    if message.chat.type == "private":
        return False
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        return False

def start_scheduler():
    scheduler.start()

@router.message(Command("schedule"))
async def set_schedule(message: types.Message, bot: Bot):
    if not await is_admin(message):
        return

    try:
        parts = message.text.split(maxsplit=2)
        minutes = int(parts[1])
        text = parts[2]
    except:
        await message.reply("Dùng: /schedule <phút> <nội_dung>")
        return

    chat_id = message.chat.id

    if chat_id in group_jobs:
        scheduler.remove_job(group_jobs[chat_id])

    async def send_msg():
        if chat_id in group_last_message:
            try:
                await bot.delete_message(chat_id, group_last_message[chat_id])
            except:
                pass
        
        sent_msg = await bot.send_message(chat_id, text)
        group_last_message[chat_id] = sent_msg.message_id

    job_id = f"schedule_{chat_id}"
    job = scheduler.add_job(send_msg, "interval", minutes=minutes, id=job_id)
    group_jobs[chat_id] = job.id

    await message.answer(f"Đã đặt tin nhắn định kỳ mỗi {minutes} phút.\nTin nhắn cũ sẽ được xóa trước khi gửi tin nhắn mới.")

@router.message(Command("unschedule"))
async def remove_schedule(message: types.Message):
    if not await is_admin(message):
        return

    chat_id = message.chat.id

    if chat_id in group_jobs:
        scheduler.remove_job(group_jobs[chat_id])
        del group_jobs[chat_id]
        
        if chat_id in group_last_message:
            try:
                await message.bot.delete_message(chat_id, group_last_message[chat_id])
            except:
                pass
            del group_last_message[chat_id]
        
        await message.answer("Đã tắt tin nhắn định kỳ.")
