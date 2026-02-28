from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()
locks = {}

async def is_admin(message: types.Message):
    """Kiểm tra nếu người dùng là admin hoặc creator"""
    # Kiểm tra nếu là private chat thì không cho dùng lệnh admin
    if message.chat.type == "private":
        return False
    
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        # Nếu bot không có quyền lấy thông tin thành viên
        return False

@router.message(Command("locklink"))
async def lock_link(message: types.Message):
    if not await is_admin(message):
        return

    locks[message.chat.id] = True
    await message.answer("Đã bật chặn link.")

@router.message(Command("unlocklink"))
async def unlock_link(message: types.Message):
    if not await is_admin(message):
        return

    locks[message.chat.id] = False
    await message.answer("Đã tắt chặn link.")

@router.message(F.text & ~F.text.startswith("/"))
async def check_links(message: types.Message):
    if locks.get(message.chat.id):
        if message.text and ("http://" in message.text or "https://" in message.text):
            await message.delete()
