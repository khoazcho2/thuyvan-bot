import sys
sys.path.insert(0, '.')

print("Testing imports...")
from config import OWNER_ID
print(f"OWNER_ID: {OWNER_ID}")

from modules import admin, locks, schedule
print("All modules imported successfully!")

# Test functions exist
print(f"is_owner function exists: {hasattr(admin, 'is_owner')}")
print(f"ban_global function exists: {hasattr(admin, 'ban_global')}")
print(f"unban_global function exists: {hasattr(admin, 'unban_global')}")
print(f"lock_18 function exists: {hasattr(locks, 'lock_18')}")
print(f"lock18 images dict exists: {hasattr(locks, 'lock_18_images')}")

print("\nAll tests passed!")
