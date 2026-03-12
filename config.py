import os

TOKEN = os.getenv("BOT_TOKEN", "").strip()


# ID của người tạo bot (người duy nhất dùng được lệnh /banglobal)
OWNER_ID = int(os.getenv("OWNER_ID", "8337495954"))
