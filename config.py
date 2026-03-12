import os

TOKEN = os.getenv("BOT_TOKEN").strip()

# Safe OWNER_ID parse - Railway env format ' =8337495954'
owner_str = os.getenv("OWNER_ID")
if owner_str:
    # Remove leading '=' if Railway format
    owner_str = owner_str.lstrip(' =')
OWNER_ID = int(owner_str or "8337495954")
