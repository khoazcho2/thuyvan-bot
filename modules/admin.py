from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import timedelta, timezone, datetime
from config import OWNER_ID
import logging

router = Router()
logger = logging.getLogger(__name__)

# Sử dụng bot_groups từ global_ban module (sẽ được import động)
bot_groups = None

async def is_owner(message: types.Message):
    """Kiểm tra nếu người dùng là người tạo bot"""
    return message.from_user.id == OWNER_ID

async def is_owner_or_admin(message: types.Message):
    """Kiểm tra nếu người dùng là chủ group hoặc admin"""
    if message.chat.type == "private":
        return False
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra admin: {e}")
        return False

@router.message(Command("ping"))
async def ping_cmd(message: types.Message):
    """Kiểm tra Bot có hoạt động trong nhóm không"""
    try:
        sent_msg = await message.answer("✅ Bot đang hoạt động!\n\nChat ID: {}\nChat Type: {}".format(
            message.chat.id,
            message.chat.type
        ))
        logger.info(f"Ping thành công tại nhóm {message.chat.id}")
    except Exception as e:
        await message.answer(f"❌ Bot gặp lỗi: {str(e)}")
        logger.error(f"Lỗi ping tại nhóm {message.chat.id}: {e}")

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    logger.info(f"Bot started trong chat {message.chat.id} - type: {message.chat.type}")
    await message.answer("Xin chào! Bot quản lý group đang hoạt động.\n\nDùng /help để xem các lệnh có sẵn.")

@router.message(Command("help"))
async def help_cmd(message: types.Message):
    # Allow in private for owner, or group admin
    if message.chat.type == "private" and not message.from_user.id == OWNER_ID:
        await message.answer("❌ /help chỉ admin group hoặc owner dùng được!")
        return
    
    help_text = """<b>📋 DANH SÁCH LỆNH ĐẦY ĐỦ</b>

<i>🔐 Admin (Chủ group hoặc admin):</i>
/ban - Ban user (reply)
/unban - Unban user (reply)
/mute [phút|giây] - Mute user (reply)
/   VD: /mute 5 (5 phút) hoặc /mute 30s (30 giây)
/locklink - Bật chặn link
/unlocklink - Tắt chặn link
/lock18 - Bật chặn 18+ (ảnh + link)
/unlock18 - Tắt chặn 18+
/lock18image - Bật chặn ảnh 18+
/unlock18image - Tắt chặn ảnh 18+
/lock18link - Bật chặn link 18+
/unlock18link - Tắt chặn link 18+
/schedule [phút] [nội_dung] - Tin nhắn định kỳ
/unschedule - Tắt tin nhắn định kỳ

<i>⚠️ Cảnh Báo (Chủ group hoặc admin):</i>
/canhbao - Cảnh báo user (reply)
/xcanhbao - Xóa tin nhắn và cảnh báo (reply)
/gocanhbao - Xóa tất cả cảnh báo (reply)
/xemcanhbao - Xem số cảnh báo (reply)

<i>👑 Bot Owner:</i>
/banglobal - Ban global (reply) - Tất cả nhóm
/unbanglobal - Unban global (reply)
/dsglobal - Danh sách global ban
/globalgroup [tin nhắn] - Gửi tin nhắn đến tất cả các nhóm

<i>📱 Khác:</i>
/start - Kiểm tra bot
/ping - Ping bot
/help - Xem danh sách lệnh"""
    await message.answer(help_text)

@router.message(Command("ban"))
async def ban_user(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần ban.")
        return

    user_id = message.reply_to_message.from_user.id
    await message.chat.ban(user_id)
    await message.answer("Đã ban user.")

@router.message(Command("unban"))
async def unban_user(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần unban.")
        return

    user_id = message.reply_to_message.from_user.id
    await message.chat.unban(user_id)
    await message.answer("Đã unban user.")

@router.message(Command("mute"))
async def mute_user(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần mute.")
        return

    try:
        parts = message.text.split()
        time_value = parts[1]
        
        if time_value.endswith("s"):
            seconds = int(time_value[:-1])
            minutes = 0
            remaining_seconds = seconds
        elif time_value.endswith("m"):
            minutes = int(time_value[:-1])
            remaining_seconds = 0
        else:
            minutes = int(time_value)
            remaining_seconds = 0
    except:
        await message.reply("Dung: /mute <so_phut> hoac /mute <so_giay>s (reply vao user)")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"

    vietnam_tz = timezone(timedelta(hours=7))
    utc_time = message.date.replace(tzinfo=timezone.utc)
    vietnam_time = utc_time.astimezone(vietnam_tz)
    until_date = vietnam_time + timedelta(minutes=minutes, seconds=remaining_seconds)

    try:
        await message.chat.restrict(
            user_id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        remaining = until_date - vietnam_time
        total_seconds = int(remaining.total_seconds())
        
        if total_seconds >= 3600:
            hours = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            countdown_text = f"{hours} gio {mins} phut"
        elif total_seconds >= 60:
            mins = total_seconds // 60
            secs = total_seconds % 60
            countdown_text = f"{mins} phut {secs} giay"
        else:
            countdown_text = f"{total_seconds} giay"
        
        if time_value.endswith("s"):
            time_display = time_value
        elif time_value.endswith("m"):
            time_display = time_value
        else:
            time_display = f"{minutes} phut"
        
        await message.answer(
            f"✅ <b>Đã mute thành công!</b>\n\n"
            f"👤 User: {user_name}\n"
            f"⏰ Thoi gian: {time_display}\n"
            f"⏱️ Con: {countdown_text}"
        )
        
        try:
            await message.chat.send_message(
                user_id,
                f"🔇 <b>Ban Đã Bị mute trong group!</b>\n\n"
                f"⏰ Thoi gian: {time_display}\n"
                f"⏱️ Con: {countdown_text}\n\n"
                f"Lien he admin de duoc unmute som hon."
            )
        except:
            pass
            
    except Exception as e:
        await message.answer(f"❌ Lỗi khi mute: {str(e)}")

# ================= WARNING SYSTEM =================

user_warnings = {}

@router.message(Command("canhbao"))
async def canh_bao(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần cảnh cáo.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    if user_id not in user_warnings:
        user_warnings[user_id] = {}
    if chat_id not in user_warnings[user_id]:
        user_warnings[user_id][chat_id] = 0
    
    user_warnings[user_id][chat_id] += 1
    warning_count = user_warnings[user_id][chat_id]
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    await message.answer(
        f"⚠️ <b>Cảnh báo!</b>\n\n"
        f"👤 User: {user_name}\n"
        f"📊 Số cảnh cáo: {warning_count}/5\n\n"
        f"<i>Lưu ý: Khi đạt 5 cảnh cáo, user sẽ bị ban khỏi nhóm.</i>"
    )

@router.message(Command("xcanhbao"))
async def xoa_va_canh_bao(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào tin nhắn cần xóa và cảnh cáo.")
        return

    try:
        await message.reply_to_message.delete()
    except:
        pass

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    if user_id not in user_warnings:
        user_warnings[user_id] = {}
    if chat_id not in user_warnings[user_id]:
        user_warnings[user_id][chat_id] = 0
    
    user_warnings[user_id][chat_id] += 1
    warning_count = user_warnings[user_id][chat_id]
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    await message.answer(
        f"⚠️ <b>Đã xóa tin nhắn và cảnh cáo!</b>\n\n"
        f"👤 User: {user_name}\n"
        f"📊 Số cảnh cáo: {warning_count}/5\n\n"
        f"<i>Lưu ý: Khi đạt 5 cảnh cáo, user sẽ bị ban khỏi nhóm.</i>"
    )
    
    if warning_count >= 5:
        try:
            await message.chat.ban(user_id)
            await message.answer(
                f"⛔ <b>User {user_name} đã bị ban!</b>\n\n"
                f"User đã đạt tối đa 5 cảnh cáo."
            )
            user_warnings[user_id][chat_id] = 0
        except:
            pass

@router.message(Command("gocanhbao"))
async def xoa_tat_ca_canh_bao(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần xóa cảnh cáo.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    if user_id in user_warnings and chat_id in user_warnings[user_id]:
        user_warnings[user_id][chat_id] = 0
        await message.answer(
            f"✅ <b>Đã xóa tất cả cảnh cáo!</b>\n\n"
            f"👤 User: {user_name}"
        )
    else:
        await message.answer(
            f"ℹ️ User {user_name} không có cảnh cáo nào."
        )

@router.message(Command("xemcanhbao"))
async def xem_canh_bao(message: types.Message):
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần xem cảnh cáo.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    warning_count = 0
    if user_id in user_warnings and chat_id in user_warnings[user_id]:
        warning_count = user_warnings[user_id][chat_id]
    
    remaining = 5 - warning_count
    
    await message.answer(
        f"📊 <b>Thông tin cảnh cáo</b>\n\n"
        f"👤 User: {user_name}\n"
        f"⚠️ Số cảnh cáo: {warning_count}/5\n"
        f"📝 Còn lại trước khi ban: {remaining}"
    )

# ================= MY CHAT MEMBER HANDLER =================

@router.my_chat_member()
async def on_bot_chat_member_update(event: types.ChatMemberUpdated):
    chat = event.chat
    new_status = event.new_chat_member.status
    
    if chat.type not in ["group", "supergroup"]:
        return
    
    if new_status == "member" or new_status == "administrator":
        bot_groups[chat.id] = True
        logger.info(f"Bot đã được thêm vào group: {chat.id} - {chat.title}")
    elif new_status == "left" or new_status == "kicked":
        if chat.id in bot_groups:
            del bot_groups[chat.id]
        logger.info(f"Bot đã bị xóa khỏi group: {chat.id}")

# ================= GLOBAL GROUP COMMAND =================

@router.message(Command("globalgroup"))
async def global_group_message(message: types.Message, bot: Bot):
    if message.chat.type != "private":
        await message.reply("⚠️ Lệnh này chỉ dùng được trong chat riêng với bot!")
        return
    
    if not await is_owner(message):
        await message.reply("⚠️ Chỉ người tạo bot mới dùng được lệnh này!")
        return
    
    text = message.text.replace("/globalgroup", "").strip()
    
    if not text:
        await message.reply(
            "📝 <b>Cách dùng lệnh /globalgroup:</b>\n\n"
            "/globalgroup [tin nhắn cần gửi]\n\n"
            "Bot sẽ gửi tin nhắn này đến TẤT CẢ các group mà bot đang tham gia.\n\n"
            "<i>Ví dụ:</i>\n"
            "/globalgroup Chào mọi người! Đây là tin nhắn thông báo từ admin."
        )
        return
    
    groups_list = list(bot_groups.keys())
    
    if not groups_list:
        await message.reply(
            "❌ Hiện tại bot không tham gia group nào!\n\n"
            "Hãy thêm bot vào các group trước."
        )
        return
    
    success_count = 0
    failed_count = 0
    failed_groups = []
    
    await message.reply(f"📤 Đang gửi tin nhắn đến {len(groups_list)} groups...")
    
    for group_id in groups_list:
        try:
            await bot.send_message(
                group_id,
                f"📢 <b>THÔNG BÁO TỪ ADMIN</b>\n\n{text}\n\n"
                f"<i> Tin nhắn này được gửi đến tất cả các nhóm.</i>"
            )
            success_count += 1
            logger.info(f"Gửi tin nhắn global thành công đến group {group_id}")
        except Exception as e:
            failed_count += 1
            failed_groups.append(group_id)
            logger.error(f"Lỗi gửi tin nhắn đến group {group_id}: {e}")
            
            if "kicked" in str(e).lower() or "forbidden" in str(e).lower():
                if group_id in bot_groups:
                    del bot_groups[group_id]
    
    result_text = f"✅ <b>Đã gửi tin nhắn thành công!</b>\n\n"
    result_text += f"📊 <b>Thống kê:</b>\n"
    result_text += f"   ✅ Thành công: {success_count} groups\n"
    
    if failed_count > 0:
        result_text += f"   ❌ Thất bại: {failed_count} groups\n"
        for gid in failed_groups:
            if gid in bot_groups:
                del bot_groups[gid]
    
    result_text += f"\n📋 Tổng số groups hiện tại: {len(bot_groups)}"
    
    await message.reply(result_text)

