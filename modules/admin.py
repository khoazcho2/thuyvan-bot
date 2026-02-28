from aiogram import Router, types, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command
from datetime import timedelta, timezone, datetime

router = Router()

async def is_owner_or_admin(message: types.Message):
    """Kiểm tra nếu người dùng là chủ group hoặc admin"""
    # Kiểm tra nếu là private chat thì không cho dùng lệnh admin
    if message.chat.type == "private":
        return False
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        # Nếu bot không có quyền lấy thông tin thành viên
        return False

@router.message(Command("start"))
async def start_cmd(message: types.Message):
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
/schedule [phut] [noi_dung] - Tin nhan dinh ky
/unschedule - Tat tin nhan dinh ky

<i>Khac:</i>
/start - Kiem tra bot
/help - Xem danh sach lenh"""
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

@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Xử lý khi có thành viên mới tham gia group"""
    for user in message.new_chat_members:
        welcome_text = f"""👋 <b>Chào mừng {user.first_name}!</b>

📜 <b>Luật nhóm:</b>  
⚔1 Không gửi link, ảnh, file bừa bãi – giữ cho không gian nhóm trong sạch  
🛒2 Không spam tin nhắn – hãy tôn trọng mọi người trong nhóm 
⏳3 Tuyệt đối không gửi bất cứ link, ảnh hay nội dung liên quan tới 18+ – giữ nhóm văn minh và lành mạnh 

Nếu cần Hỗ trợ gì ib admin : @qiaxlam

Một lần nữa, chào mừng bạn đã đến với nhóm! 🎉"""

        await message.answer(welcome_text)

@router.message(Command("setwelcome"))
async def set_welcome(message: Message, command: Command):
    """Thiết lập tin nhắn chào mừng (admin only)"""
    if not await is_owner_or_admin(message):
        await message.reply("⚠️ Chỉ chủ group hoặc admin mới dùng được lệnh này!")
        return
    
    welcome_text = message.text.replace(command.text, "").strip()
    if not welcome_text:
        await message.reply("Vui lòng nhập nội dung chào mừng.\nVí dụ: /setwelcome Chào mừng {user}!")
        return
    
    # Lưu vào config hoặc database (tạm thời lưu vào biến toàn cục)
    global custom_welcome
    custom_welcome[message.chat.id] = welcome_text
    
    await message.answer(f"✅ Đã thiết lập tin nhắn chào mừng cho nhóm này!")

# Biến lưu tin nhắn chào mừng tùy chỉnh
custom_welcome = {}
