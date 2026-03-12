from aiogram import Router, types, F
from aiogram.filters import Command
import json
import os
from datetime import datetime
from config import OWNER_ID
import logging

router = Router()
logger = logging.getLogger(__name__)

# Đường dẫn file lưu trữ danh sách ban global
DATA_DIR = "data"
GLOBAL_BAN_FILE = os.path.join(DATA_DIR, "global_ban.json")

# Đảm bảo thư mục data tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

# Danh sách user bị ban global (user_id: {"name": str, "timestamp": str})
global_banned_users = {}

# Danh sách các group mà bot đang tham gia (group_id: True)
bot_groups = {}

def load_global_ban():
    """Tải danh sách ban global từ file JSON"""
    global global_banned_users
    if os.path.exists(GLOBAL_BAN_FILE):
        try:
            with open(GLOBAL_BAN_FILE, "r", encoding="utf-8") as f:
                global_banned_users = json.load(f)
            logger.info(f"Đã tải {len(global_banned_users)} user từ danh sách ban global")
        except Exception as e:
            logger.error(f"Lỗi khi tải danh sách ban global: {e}")
            global_banned_users = {}
    else:
        global_banned_users = {}

def save_global_ban():
    """Lưu danh sách ban global vào file JSON"""
    try:
        with open(GLOBAL_BAN_FILE, "w", encoding="utf-8") as f:
            json.dump(global_banned_users, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu {len(global_banned_users)} user vào danh sách ban global")
    except Exception as e:
        logger.error(f"Lỗi khi lưu danh sách ban global: {e}")

# Tải danh sách ban global khi khởi động module
load_global_ban()

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

async def is_global_banned(user_id: int) -> bool:
    """Kiểm tra user có bị ban global không"""
    return str(user_id) in global_banned_users

async def ban_global_user(user_id: int, user_name: str):
    """Thêm user vào danh sách ban global"""
    global_banned_users[str(user_id)] = {
        "name": user_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_global_ban()

async def unban_global_user(user_id: int):
    """Xóa user khỏi danh sách ban global"""
    if str(user_id) in global_banned_users:
        del global_banned_users[str(user_id)]
        save_global_ban()
        return True
    return False

@router.message(Command("banglobal"))
async def ban_global(message: types.Message):
    """Lệnh ban global - chỉ người tạo bot mới dùng được"""
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
        user_name = f"@{user.username} ({user.first_name})"
    
    # Kiểm tra user đã bị ban global chưa
    if str(user_id) in global_banned_users:
        await message.reply(f"⚠️ User {user_name} đã bị ban global trước đó rồi!")
        return
    
    # Thêm vào danh sách ban global
    await ban_global_user(user_id, user_name)
    
    # Gửi xác nhận cho owner
    await message.answer(
        f"✅ <b>Đã ban global thành công!</b>\n\n"
        f"👤 User: {user_name}\n"
        f"🆔 ID: {user_id}\n"
        f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🔇 User sẽ bị mute vĩnh viễn trên tất cả các nhóm\n"
        f"⛔ User sẽ bị ban vĩnh viễn trên tất cả các nhóm"
    )

@router.message(Command("unbanglobal"))
async def unban_global(message: types.Message):
    """Lệnh unban global - chỉ người tạo bot mới dùng được"""
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
    if await unban_global_user(user_id):
        await message.answer(
            f"✅ <b>Đã unban global!</b>\n\n"
            f"👤 User: {user_name} (ID: {user_id})"
        )
    else:
        await message.reply(f"⚠️ User {user_name} không có trong danh sách ban global!")

@router.message(Command("dsglobal"))
async def danh_sach_global(message: types.Message):
    """Lệnh xem danh sách ban global - chỉ người tạo bot mới dùng được"""
    if not await is_owner(message):
        await message.reply("⚠️ Chỉ người tạo bot mới dùng được lệnh này!")
        return
    
    if not global_banned_users:
        await message.reply("📝 Danh sách ban global hiện đang trống!")
        return
    
    # Tạo danh sách
    text = "<b>📋 DANH SÁCH BAN GLOBAL</b>\n\n"
    
    for user_id, info in global_banned_users.items():
        text += f"• <b>{info['name']}</b> (ID: {user_id})\n"
        text += f"   ⏰ Bị ban lúc: {info['timestamp']}\n\n"
    
    text += f"📊 Tổng số: <b>{len(global_banned_users)}</b> user"
    
    await message.answer(text)

@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Xử lý khi có thành viên mới tham gia group - AUTO BAN"""
    for user in message.new_chat_members:
        # Kiểm tra user bị ban global
        if await is_global_banned(user.id):
            try:
                # Ban user
                await message.chat.ban(user.id)
                # Mute vĩnh viễn
                await message.chat.restrict(
                    user.id,
                    permissions=types.ChatPermissions(can_send_messages=False)
                )
                await message.answer(
                    f"⛔ <b>User {user.first_name} đã bị BAN GLOBAL!</b>\n\n"
                    f"👤 User này đã bị ban khỏi tất cả các nhóm.\n"
                    f"🆔 ID: {user.id}\n\n"
                    f"Liên hệ @qiaxlam để biết thêm chi tiết."
                )
                logger.info(f"Đã ban global user {user.id} - {user.first_name} tại group {message.chat.id}")
                continue
            except Exception as e:
                logger.error(f"Lỗi khi ban global user {user.id}: {e}")
                pass
        
        # Welcome message cho user bình thường
        welcome_text = f"""👋 <b>Chào mừng {user.first_name}!</b>

📜 <b>Luật nhóm:</b>  
⚔1 Không gửi link, ảnh, file bừa bãi – giữ cho không gian nhóm trong sạch  
🛒2 Không spam tin nhắn – hãy tôn trọng mọi người trong nhóm 
⏳3 Tuyệt đối không gửi bất cứ link, ảnh hay nội dung liên quan tới 18+ – giữ nhóm văn minh và lành mạnh 

Nếu cần Hỗ trợ gì ib admin : @qiaxlam

Một lần nữa, chào mừng bạn đã đến với nhóm! 🎉"""

        await message.answer(welcome_text)

@router.message()
async def check_global_banned_message(message: types.Message):
    """Kiểm tra tin nhắn từ user bị ban global - AUTO BAN khi gửi tin nhắn"""
    # Chỉ kiểm tra trong group
    if message.chat.type == "private":
        return
    
    # Bỏ qua nếu là admin
    if await is_owner_or_admin(message):
        return
    
    user_id = message.from_user.id
    
    # Kiểm tra user có bị ban global không
    if await is_global_banned(user_id):
        try:
            # Ban user
            await message.chat.ban(user_id)
            # Xóa tin nhắn của user
            await message.delete()
            
            user_name = message.from_user.first_name
            if message.from_user.username:
                user_name = f"@{message.from_user.username}"
            
            await message.answer(
                f"⛔ <b>User {user_name} đã bị BAN GLOBAL!</b>\n\n"
                f"👤 User này đã bị ban khỏi tất cả các nhóm do vi phạm nghiêm trọng.\n"
                f"🆔 ID: {user_id}\n\n"
                f"Liên hệ @qiaxlam để biết thêm chi tiết."
            )
            logger.info(f"Đã ban global user {user_id} - {user_name} tại group {message.chat.id} (do gửi tin nhắn)")
        except Exception as e:
            logger.error(f"Lỗi khi ban global user {user_id}: {e}")

# ================= MY CHAT MEMBER HANDLER =================

@router.my_chat_member()
async def on_bot_chat_member_update(event: types.ChatMemberUpdated):
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
        
        # Quét tất cả thành viên trong group để kiểm tra global ban
        try:
            await scan_group_members(chat)
        except Exception as e:
            logger.error(f"Lỗi khi quét thành viên group {chat.id}: {e}")
            
    elif new_status == "left" or new_status == "kicked":
        # Bot bị xóa khỏi group
        if chat.id in bot_groups:
            del bot_groups[chat.id]
        logger.info(f"Bot đã bị xóa khỏi group: {chat.id}")

async def scan_group_members(chat):
    """Quét tất cả thành viên trong group và ban các user bị global ban"""
    try:
        from aiogram.types import ChatMemberMember, ChatMemberAdministrator, ChatMemberCreator
        
        # Lấy danh sách thành viên
        members = []
        try:
            # Thử lấy tất cả thành viên (chỉ hoạt động nếu bot là admin)
            async for member in chat.get_members():
                members.append(member)
        except:
            # Nếu không lấy được, thử cách khác
            try:
                # Lấy thông tin user từ tin nhắn gần đây
                pass
            except:
                pass
        
        banned_count = 0
        
        for member in members:
            # Bỏ qua bot và admin
            if member.user.is_bot:
                continue
            
            try:
                # Kiểm tra xem có phải admin không
                member_info = await chat.get_member(member.user.id)
                if member_info.status in ["creator", "administrator"]:
                    continue
            except:
                pass
            
            # Kiểm tra user có bị global ban không
            if await is_global_banned(member.user.id):
                try:
                    # Ban user
                    await chat.ban(member.user.id)
                    # Mute vĩnh viễn
                    await chat.restrict(
                        member.user.id,
                        permissions=types.ChatPermissions(can_send_messages=False)
                    )
                    banned_count += 1
                    logger.info(f"Đã ban global user {member.user.id} - {member.user.first_name} trong group {chat.id} (quét)")
                except Exception as e:
                    logger.error(f"Lỗi khi ban user {member.user.id}: {e}")
        
        if banned_count > 0:
            await chat.send_message(
                f"⛔ <b>Đã ban {banned_count} user bị global ban!</b>\n\n"
                f"Các user này đã bị ban khỏi tất cả các nhóm."
            )
            
    except Exception as e:
        logger.error(f"Lỗi khi quét thành viên group: {e}")

