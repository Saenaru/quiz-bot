import logging
from telegram import Update
from telegram.ext import Application, CommandHandler
from config import TOKEN
from handlers import get_conversation_handler, help_command

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = get_conversation_handler()
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    logger.info("Бот запускается...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
