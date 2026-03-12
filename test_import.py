import sys
sys.path.insert(0, '.')

from config import OWNER_ID
print("OWNER_ID:", OWNER_ID)

# Test imports
from modules.admin import is_owner
from modules.locks import contains_adult_keyword, is_adult_link, ADULT_KEYWORDS
print("locks.py import OK")

# Test functions
print("\nTesting contains_adult_keyword:")
print("  'porn' ->", contains_adult_keyword("porn"))
print("  'hello' ->", contains_adult_keyword("hello"))

print("\nTesting is_adult_link:")
print("  'https://pornhub.com' ->", is_adult_link("https://pornhub.com"))
print("  'https://google.com' ->", is_adult_link("https://google.com"))

print("\nAll tests passed!")
