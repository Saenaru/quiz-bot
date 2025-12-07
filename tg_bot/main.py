import logging
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

from telegram import Update
from telegram.ext import Application, CommandHandler
from config import TOKEN
import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    application = Application.builder().token(TOKEN).build()
    conv_handler = handlers.get_conversation_handler()
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', handlers.help_command))
    logger.info("Telegram бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
