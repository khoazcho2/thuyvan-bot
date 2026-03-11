from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import timedelta, timezone, datetime
from config import OWNER_ID
from modules import schedule
import logging

router = Router()
logger = logging.getLogger(__name__)

# Danh sách user bị ban global (user_id: True)
global_banned_users = {}

# Danh sách các group mà bot đang tham gia (group_id: True)
bot_groups = {}

async def is_owner(message: types.Message):
    """Kiểm tra nếu người dùng là người tạo bot"""
    return message.from_user.id == OWNER_ID

async def is_owner_or_admin(message: types.Message):
    """Kiểm tra nếu người dùng là chủ group hoặc admin"""
    # Kiểm tra nếu là private chat thì không cho dùng lệnh admin
    if message.chat.type == "private":
        return False
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra admin: {e}")
        # Nếu bot không có quyền lấy thông tin thành viên
        return False

@router.message(Command("ping"))
async def ping_cmd(message: types.Message):
    """Kiểm tra Bot có hoạt động trong nhóm không"""
    # Thử gửi tin nhắn để kiểm tra
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
    help_text = """<b>Cac lenh co san:</b>

<i>Admin (Chi chu group hoac admin):</i>
/ban - Ban user (reply)
/unban - Unban user (reply)
/mute [phut|giay] - Mute user (reply)
   VD: /mute 5 (5 phut) hoac /mute 30s (30 giay)
/locklink - Bat chan link
/unlocklink - Tat chan link
/lock18 - Bat chan 18+ (anh + link)
/unlock18 - Tat chan 18+
/lock18image - Bat chan anh 18+
/unlock18image - Tat chan anh 18+
/lock18link - Bat chan link 18+
/unlock18link - Tat chan link 18+
/schedule [phut] [noi_dung] - Tin nhan dinh ky
/unschedule - Tat tin nhan dinh ky

<i>Canh Bao (Chi chu group hoac admin):</i>
/canhbao - Canh bao user (reply)
/xcanhbao - Xoa tin nhan va canh bao (reply)
/gocanhbao - Xoa tat ca canh bao (reply)
/xemcanhbao - Xem so canh bao (reply)

<i>Bot Owner (Chi nguoi tao bot):</i>
/banglobal - Ban global (reply) - Tat ca nhom
/unbanglobal - Unban global (reply)
/globalgroup [tin nhan] - Gui tin nhan den tat ca cac nhom

<i>Khac:</i>
/start - Kiem tra bot
/help - Xem danh sach lenh"""
    
    # Tạo keyboard cho help
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Xem lệnh", url="https://t.me/")]
    ])
    await message.answer(help_text, reply_markup=keyboard)

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
        
        # Kiem tra xem la phut hay giay
        if time_value.endswith("s"):
            # Giay (vi du: 30s)
            seconds = int(time_value[:-1])
            minutes = 0
            remaining_seconds = seconds
        elif time_value.endswith("m"):
            # Phut (vi du: 5m)
            minutes = int(time_value[:-1])
            remaining_seconds = 0
        else:
            # Mac dinh la phut
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

    # Sử dụng múi giờ Việt Nam (UTC+7)
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
        
        # Tính thời gian đếm ngược
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
        
        # Hien thi thoi gian hop ly
        if time_value.endswith("s"):
            time_display = time_value
        elif time_value.endswith("m"):
            time_display = time_value
        else:
            time_display = f"{minutes} phut"
        
        # Xác nhận cho admin (hiển thị đếm ngược)
        await message.answer(
            f"✅ <b>Đã mute thành công!</b>\n\n"
            f"👤 User: {user_name}\n"
            f"⏰ Thoi gian: {time_display}\n"
            f"⏱️ Con: {countdown_text}"
        )
        
        # Gửi tin nhắn cho user bị mute (nếu là group)
        try:
            await message.chat.send_message(
                user_id,
                f"🔇 <b>Ban Đã Bị mute trong group!</b>\n\n"
                f"⏰ Thoi gian: {time_display}\n"
                f"⏱️ Con: {countdown_text}\n\n"
                f"Lien he admin de duoc unmute som hon."
            )
        except:
            pass  # Có thể user không nhận được tin nhắn
            
    except Exception as e:
        await message.answer(f"❌ Lỗi khi mute: {str(e)}")

@router.message(Command("banglobal"))
async def ban_global(message: types.Message):
    """Lệnh ban global - chỉ người tạo bot mới dùng được"""
    # Kiểm tra nếu không phải chủ bot
    if not await is_owner(message):
        await message.reply("⚠️ Chỉ người tạo bot mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần ban global.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    # Thêm vào danh sách ban global
    global_banned_users[user_id] = True
    
    # Gửi xác nhận cho owner
    await message.answer(
        f"✅ <b>Đã ban global thành công!</b>\n\n"
        f"👤 User: {user_name} (ID: {user_id})\n"
        f"🔇 Tình trạng: Bị mute vĩnh viễn trên tất cả các nhóm\n"
        f"⛔ Tình trạng: Bị ban vĩnh viễn trên tất cả các nhóm"
    )

@router.message(Command("unbanglobal"))
async def unban_global(message: types.Message):
    """Lệnh unban global - chỉ người tạo bot mới dùng được"""
    # Kiểm tra nếu không phải chủ bot
    if not await is_owner(message):
        await message.reply("⚠️ Chỉ người tạo bot mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần unban global.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    # Xóa khỏi danh sách ban global
    if user_id in global_banned_users:
        del global_banned_users[user_id]
    
    await message.answer(
        f"✅ <b>Đã unban global!</b>\n\n"
        f"👤 User: {user_name}"
    )

@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Xử lý khi có thành viên mới tham gia group"""
    for user in message.new_chat_members:
        # Kiểm tra user bị ban global
        if user.id in global_banned_users:
            try:
                await message.chat.ban(user.id)
                await message.chat.restrict(
                    user.id,
                    permissions=types.ChatPermissions(can_send_messages=False)
                )
                await message.answer(
                    f"⛔ User {user.first_name} đã bị ban global và không được phép tham gia nhóm này."
                )
                continue  # Bỏ qua welcome message cho user bị ban global
            except:
                pass
        
        welcome_text = f"""👋 <b>Chào mừng {user.first_name}!</b>

📜 <b>Luật nhóm:</b>  
⚔1 Không gửi link, ảnh, file bừa bãi – giữ cho không gian nhóm trong sạch  
🛒2 Không spam tin nhắn – hãy tôn trọng mọi người trong nhóm 
⏳3 Tuyệt đối không gửi bất cứ link, ảnh hay nội dung liên quan tới 18+ – giữ nhóm văn minh và lành mạnh 

Nếu cần Hỗ trợ gì ib admin : @qiaxlam

Một lần nữa, chào mừng bạn đã đến với nhóm! 🎉"""

        await message.answer(welcome_text)

# Biến lưu tin nhắn chào mừng tùy chỉnh
custom_welcome = {}

# ================= WARNING SYSTEM =================
# Lưu cảnh cáo của user (user_id: {"chat_id": số_lần_cảnh_báo})
user_warnings = {}

# Hàm tạo keyboard cho lệnh cảnh cáo
def get_warning_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Xóa cảnh cáo", callback_data=f"remove_warning_{user_id}"),
            InlineKeyboardButton(text="📊 Xem cảnh cáo", callback_data=f"view_warning_{user_id}")
        ]
    ])

# Callback query handler cho các nút bấm
@router.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    """Xử lý khi bấm nút"""
    data = callback.data
    
    if not callback.message:
        await callback.answer("❌ Không tìm thấy tin nhắn!", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    # Kiểm tra admin
    try:
        member = await callback.message.chat.get_member(user_id)
        if member.status not in ["creator", "administrator"]:
            await callback.answer("⚠️ Chỉ admin mới dùng được!", show_alert=True)
            return
    except:
        await callback.answer("❌ Lỗi kiểm tra quyền!", show_alert=True)
        return
    
    # Xử lý xóa cảnh cáo
    if data.startswith("remove_warning_"):
        target_user_id = int(data.replace("remove_warning_", ""))
        
        if target_user_id in user_warnings and chat_id in user_warnings[target_user_id]:
            user_warnings[target_user_id][chat_id] = 0
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ <b>Đã xóa cảnh cáo!</b>"
            )
            await callback.answer("Đã xóa cảnh cáo!", show_alert=True)
        else:
            await callback.answer("User không có cảnh cáo!", show_alert=True)
    
    # Xử lý xem cảnh cáo
    elif data.startswith("view_warning_"):
        target_user_id = int(data.replace("view_warning_", ""))
        
        warning_count = 0
        if target_user_id in user_warnings and chat_id in user_warnings[target_user_id]:
            warning_count = user_warnings[target_user_id][chat_id]
        
        remaining = 5 - warning_count
        await callback.message.edit_text(
            f"📊 <b>Thông tin cảnh cáo</b>\n\n⚠️ Số cảnh cáo: {warning_count}/5\n📝 Còn lại trước khi ban: {remaining}"
        )
        await callback.answer()

@router.message(Command("canhbao"))
async def canh_bao(message: types.Message):
    """Cảnh cáo một người dùng"""
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào người cần cảnh cáo.")
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    # Khởi tạo nếu chưa có
    if user_id not in user_warnings:
        user_warnings[user_id] = {}
    if chat_id not in user_warnings[user_id]:
        user_warnings[user_id][chat_id] = 0
    
    # Tăng số cảnh cáo
    user_warnings[user_id][chat_id] += 1
    warning_count = user_warnings[user_id][chat_id]
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    keyboard = get_warning_keyboard(user_id)
    
    await message.answer(
        f"⚠️ <b>Cảnh báo!</b>\n\n👤 User: {user_name}\n📊 Số cảnh cáo: {warning_count}/5\n\n<i>Lưu ý: Khi đạt 5 cảnh cáo, user sẽ bị ban khỏi nhóm.</i>",
        reply_markup=keyboard
    )

@router.message(Command("xcanhbao"))
async def xoa_va_canh_bao(message: types.Message):
    """Xóa tin nhắn được trả lời và cảnh cáo người gửi"""
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return

    if not message.reply_to_message:
        await message.reply("Reply vào tin nhắn cần xóa và cảnh cáo.")
        return

    # Xóa tin nhắn được reply
    try:
        await message.reply_to_message.delete()
    except:
        pass

    user = message.reply_to_message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    # Khởi tạo nếu chưa có
    if user_id not in user_warnings:
        user_warnings[user_id] = {}
    if chat_id not in user_warnings[user_id]:
        user_warnings[user_id][chat_id] = 0
    
    # Tăng số cảnh cáo
    user_warnings[user_id][chat_id] += 1
    warning_count = user_warnings[user_id][chat_id]
    
    user_name = user.first_name
    if user.username:
        user_name = f"@{user.username}"
    
    keyboard = get_warning_keyboard(user_id)
    
    await message.answer(
        f"⚠️ <b>Đã xóa tin nhắn và cảnh cáo!</b>\n\n👤 User: {user_name}\n📊 Số cảnh cáo: {warning_count}/5\n\n<i>Lưu ý: Khi đạt 5 cảnh cáo, user sẽ bị ban khỏi nhóm.</i>",
        reply_markup=keyboard
    )
    
    # Kiểm tra nếu đạt 5 cảnh cáo thì ban
    if warning_count >= 5:
        try:
            await message.chat.ban(user_id)
            await message.answer(
                f"⛔ <b>User {user_name} đã bị ban!</b>\n\nUser đã đạt tối đa 5 cảnh cáo."
            )
            # Xóa cảnh cáo sau khi ban
            user_warnings[user_id][chat_id] = 0
        except:
            pass

@router.message(Command("gocanhbao"))
async def xoa_tat_ca_canh_bao(message: types.Message):
    """Xóa tất cả cảnh cáo của một người dùng"""
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
            f"✅ <b>Đã xóa tất cả cảnh cáo!</b>\n\n👤 User: {user_name}"
        )
    else:
        await message.answer(
            f"ℹ️ User {user_name} không có cảnh cáo nào."
        )

@router.message(Command("xemcanhbao"))
async def xem_canh_bao(message: types.Message):
    """Hiển thị cảnh cáo của một người dùng"""
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
    
    keyboard = get_warning_keyboard(user_id)
    
    await message.answer(
        f"📊 <b>Thông tin cảnh cáo</b>\n\n👤 User: {user_name}\n⚠️ Số cảnh cáo: {warning_count}/5\n📝 Còn lại trước khi ban: {remaining}",
        reply_markup=keyboard
    )

# ================= MY CHAT MEMBER HANDLER =================
# Theo dõi khi bot được thêm vào/xóa khỏi groups

@router.my_chat_member()
async def on_bot_chat_member_update(event: types.MyChatMemberUpdated):
    """Xử lý khi trạng thái bot trong chat thay đổi"""
    chat = event.chat
    new_status = event.new_chat_member.status
    
    # Chỉ quan tâm đến các group/supergroup
    if chat.type not in ["group", "supergroup"]:
        return
    
    if new_status == "member" or new_status == "administrator":
        # Bot được thêm vào group
        bot_groups[chat.id] = True
        logger.info(f"Bot đã được thêm vào group: {chat.id} - {chat.title}")
    elif new_status == "left" or new_status == "kicked":
        # Bot bị xóa khỏi group
        if chat.id in bot_groups:
            del bot_groups[chat.id]
        logger.info(f"Bot đã bị xóa khỏi group: {chat.id}")

# ================= GLOBAL GROUP COMMAND =================

@router.message(Command("globalgroup"))
async def global_group_message(message: types.Message, bot: types.Bot):
    """Gửi tin nhắn đến tất cả các group - Chỉ owner dùng được"""
    # Chỉ cho phép trong private chat
    if message.chat.type != "private":
        await message.reply("⚠️ Lệnh này chỉ dùng được trong chat riêng với bot!")
        return
    
    # Kiểm tra nếu không phải chủ bot
    if not await is_owner(message):
        await message.reply("⚠️ Chỉ người tạo bot mới dùng được lệnh này!")
        return
    
    # Lấy nội dung tin nhắn (bỏ qua lệnh /globalgroup)
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
    
    # Lấy danh sách các group
    groups_list = list(bot_groups.keys())
    
    if not groups_list:
        await message.reply(
            "❌ Hiện tại bot không tham gia group nào!\n\n"
            "Hãy thêm bot vào các group trước."
        )
        return
    
    # Gửi tin nhắn đến tất cả các group
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
            
            # Nếu bot bị kick khỏi group thì xóa khỏi danh sách
            if "kicked" in str(e).lower() or "forbidden" in str(e).lower():
                if group_id in bot_groups:
                    del bot_groups[group_id]
    
    # Gửi kết quả cho owner
    result_text = f"✅ <b>Đã gửi tin nhắn thành công!</b>\n\n"
    result_text += f"📊 <b>Thống kê:</b>\n"
    result_text += f"   ✅ Thành công: {success_count} groups\n"
    
    if failed_count > 0:
        result_text += f"   ❌ Thất bại: {failed_count} groups\n"
        # Xóa các group thất bại khỏi danh sách
        for gid in failed_groups:
            if gid in bot_groups:
                del bot_groups[gid]
    
    result_text += f"\n📋 Tổng số groups hiện tại: {len(bot_groups)}"
    
    await message.reply(result_text)

