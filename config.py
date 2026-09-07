import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = os.getenv("PREFIX", "!")

# TikTok defaults
STREAK_MESSAGE = os.getenv("STREAK_MESSAGE", "🔥 Streak Reminder 🔥")
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
PAGE_LOAD_WAIT = int(os.getenv("PAGE_LOAD_WAIT", "5"))
ELEMENT_WAIT = int(os.getenv("ELEMENT_WAIT", "3"))
MESSAGE_SEND_DELAY = int(os.getenv("MESSAGE_SEND_DELAY", "2"))

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
COOKIES_FILE = os.path.join(DATA_DIR, "cookies.json")
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

TIKTOK_MESSAGES_URL = "https://www.tiktok.com/messages"
