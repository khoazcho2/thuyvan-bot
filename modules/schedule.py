from aiogram import Router, types, Bot
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

router = Router()
scheduler = AsyncIOScheduler()

group_jobs = {}
group_last_message = {}

# ================= ADMIN CHECK =================

async def is_admin(message: types.Message):
    if message.chat.type == "private":
        return False

    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except:
        return False

# ================= START SCHEDULER =================

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

# ================= SET SCHEDULE =================

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

    # Nếu đã có job cũ thì xóa
    if chat_id in group_jobs:
        scheduler.remove_job(group_jobs[chat_id])

    async def send_msg():
        # Xóa tin nhắn cũ nếu có
        if chat_id in group_last_message:
            try:
                await bot.delete_message(chat_id, group_last_message[chat_id])
            except:
                pass

        # Bỏ ghim tất cả tin nhắn cũ
        try:
            await bot.unpin_all_chat_messages(chat_id)
        except:
            pass

        # Gửi tin nhắn mới
        sent_msg = await bot.send_message(chat_id, text)

        # Ghim tin nhắn mới
        try:
            await bot.pin_chat_message(
                chat_id=chat_id,
                message_id=sent_msg.message_id,
                disable_notification=True
            )
        except:
            pass

        group_last_message[chat_id] = sent_msg.message_id

    job_id = f"schedule_{chat_id}"
    job = scheduler.add_job(
        send_msg,
        "interval",
        minutes=minutes,
        id=job_id
    )

    group_jobs[chat_id] = job.id

    await message.answer(
        f"✅ Đã đặt tin nhắn định kỳ mỗi {minutes} phút.\n"
        f"📌 Bot sẽ tự ghim tin nhắn mới và xóa tin cũ."
    )

# ================= REMOVE SCHEDULE =================

@router.message(Command("unschedule"))
async def remove_schedule(message: types.Message):
    if not await is_admin(message):
        return

    chat_id = message.chat.id

    if chat_id in group_jobs:
        scheduler.remove_job(group_jobs[chat_id])
        del group_jobs[chat_id]

        # Xóa tin nhắn cuối cùng
        if chat_id in group_last_message:
            try:
                await message.bot.delete_message(chat_id, group_last_message[chat_id])
            except:
                pass
            del group_last_message[chat_id]

        # Bỏ ghim tất cả
        try:
            await message.bot.unpin_all_chat_messages(chat_id)
        except:
            pass

        await message.answer("❌ Đã tắt tin nhắn định kỳ và bỏ ghim.")
    else:
        await message.answer("⚠️ Nhóm này chưa có tin nhắn định kỳ.")
