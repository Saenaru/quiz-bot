import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_FILE = os.getenv('DB_FILE', 'quiz_bot.db')

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env файле")