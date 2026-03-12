import os

TOKEN = os.getenv("BOT_TOKEN", "8643690918:AAEN1ENqPWmHhovnlgtEFWDtvEctX4zzm4k").strip()

# ID của người tạo bot (người duy nhất dùng được lệnh /banglobal)
OWNER_ID = int(os.getenv("OWNER_ID", "8337495954") or "0")
