import os
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', 0))
DB_FILE = os.getenv('DB_FILE', 'quiz_bot.db')

if not VK_TOKEN:
    raise ValueError("VK_TOKEN не найден в .env файле")
