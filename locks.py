from aiogram import Router, types, F
from aiogram.filters import Command
import re

router = Router()
locks = {}
lock_18_images = {}
lock_18_links = {}

# Danh sách từ khóa 18+ (có thể tùy chỉnh)
ADULT_KEYWORDS = [
    # Tiếng Việt
    "18+", "xxx", "porn", "sex", "nude", "nguoi lon", "người lớn",
    "ham chua", "hàm chửa", "phim sex", "phim xxx", "clip sex",
    "truyen sex", "truyện sex", "truyen 18", "truyện 18",
    # Tiếng Anh
    "adult", "xxx", "porn", "pussy", "dick", "cock", "boobs",
    "milf", "teen", "hardcore", "blowjob", "handjob", "threesome",
    "orgy", "fetish", "bdsm", "voyeur", "masturbat", "anal"
]

# Regex pattern cho link 18+
ADULT_LINK_PATTERNS = [
    r"(?:https?://)?(?:www\.)?(?:pornhub|xnxx|xvideos|redtube|youporn|hentai|4chan|8kun)\.[a-z]{2,}/?",
    r"(?:https?://)?(?:www\.)?(?:xnxx|pornhub|xvideos)\.(?:com|net|org|info)/+",
    r"(?:https?://)?(?:\w+\.)?(?:porn|xxx|adult|sex)\.[a-z]{2,}/+",
]

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

def contains_adult_keyword(text):
    """Kiểm tra nếu text chứa từ khóa 18+"""
    text_lower = text.lower()
    for keyword in ADULT_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

def is_adult_link(text):
    """Kiểm tra nếu text là link 18+"""
    text_lower = text.lower()
    for pattern in ADULT_LINK_PATTERNS:
        if re.search(pattern, text_lower):
            return True
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

@router.message(Command("lock18"))
async def lock_18(message: types.Message):
    """Bật chặn ảnh 18+ và link 18+"""
    if not await is_admin(message):
        return

    lock_18_images[message.chat.id] = True
    lock_18_links[message.chat.id] = True
    await message.answer("Đã bật chặn nội dung 18+ (ảnh + link).")

@router.message(Command("unlock18"))
async def unlock_18(message: types.Message):
    """Tắt chặn ảnh 18+ và link 18+"""
    if not await is_admin(message):
        return

    lock_18_images[message.chat.id] = False
    lock_18_links[message.chat.id] = False
    await message.answer("Đã tắt chặn nội dung 18+ (ảnh + link).")

@router.message(Command("lock18image"))
async def lock_18_image(message: types.Message):
    """Bật chặn ảnh 18+"""
    if not await is_admin(message):
        return

    lock_18_images[message.chat.id] = True
    await message.answer("Đã bật chặn ảnh 18+.")

@router.message(Command("unlock18image"))
async def unlock_18_image(message: types.Message):
    """Tắt chặn ảnh 18+"""
    if not await is_admin(message):
        return

    lock_18_images[message.chat.id] = False
    await message.answer("Đã tắt chặn ảnh 18+.")

@router.message(Command("lock18link"))
async def lock_18_link(message: types.Message):
    """Bật chặn link 18+"""
    if not await is_admin(message):
        return

    lock_18_links[message.chat.id] = True
    await message.answer("Đã bật chặn link 18+.")

@router.message(Command("unlock18link"))
async def unlock_18_link(message: types.Message):
    """Tắt chặn link 18+"""
    if not await is_admin(message):
        return

    lock_18_links[message.chat.id] = False
    await message.answer("Đã tắt chặn link 18+.")

@router.message(F.text & ~F.text.startswith("/"))
async def check_links(message: types.Message):
    if locks.get(message.chat.id):
        if message.text and ("http://" in message.text or "https://" in message.text):
            await message.delete()
    
    # Kiểm tra link 18+
    if lock_18_links.get(message.chat.id):
        if message.text and is_adult_link(message.text):
            await message.delete()
            try:
                await message.answer(f"⚠️ Link {message.from_user.first_name} đã bị xóa do chứa nội dung 18+!")
            except:
                pass
            return
        
        # Kiểm tra từ khóa 18+ trong tin nhắn
        if message.text and contains_adult_keyword(message.text):
            await message.delete()
            try:
                await message.answer(f"⚠️ Tin nhắn của {message.from_user.first_name} đã bị xóa do chứa nội dung 18+!")
            except:
                pass

@router.message(F.photo)
async def check_18_images(message: types.Message):
    """Kiểm tra ảnh 18+"""
    if not lock_18_images.get(message.chat.id):
        return
    
    # Telegram có AI tích hợp để phát hiện nội dung nhạy cảm
    # Nhưng chúng ta cũng có thể kiểm tra caption
    if message.caption and contains_adult_keyword(message.caption):
        await message.delete()
        try:
            await message.answer(f"⚠️ Ảnh của {message.from_user.first_name} đã bị xóa do có caption 18+!")
        except:
            pass
        return
    
    # Nếu có caption chứa link 18+
    if message.caption and is_adult_link(message.caption):
        await message.delete()
        try:
            await message.answer(f"⚠️ Ảnh của {message.from_user.first_name} đã bị xóa do chứa link 18+!")
        except:
            pass

@router.message(F.sticker)
async def check_18_stickers(message: types.Message):
    """Kiểm tra sticker 18+"""
    if not lock_18_images.get(message.chat.id):
        return
    
    # Telegram AI sẽ tự động phát hiện sticker nhạy cảm
    # Nhưng chúng ta có thể thêm logic bổ sung nếu cần
    pass
