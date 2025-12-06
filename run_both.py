import threading
import logging
import sys
import os

# Добавляем корневую директорию проекта в путь
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Добавляем пути к папкам ботов
sys.path.append(os.path.join(project_root, 'tg_bot'))
sys.path.append(os.path.join(project_root, 'vk_bot'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def run_telegram_bot():
    """Запуск Telegram бота"""
    import sys
    import os
    
    # Устанавливаем правильный путь для импортов внутри потока
    sys.path.append(os.path.join(project_root, 'tg_bot'))
    
    from tg_bot.main import main as telegram_main
    telegram_main()

def run_vk_bot():
    """Запуск VK бота"""
    import sys
    import os
    
    # Устанавливаем правильный путь для импортов
    sys.path.append(os.path.join(project_root, 'vk_bot'))
    
    from vk_bot.main import main as vk_main
    vk_main()

def main():
    logger = logging.getLogger(__name__)
    
    logger.info("Запуск обоих ботов...")
    
    # Создаем отдельный поток для Telegram бота
    telegram_thread = threading.Thread(
        target=run_telegram_bot,
        name="TelegramBotThread"
    )
    telegram_thread.daemon = True
    
    # Запускаем Telegram бот в отдельном потоке
    telegram_thread.start()
    logger.info("Telegram бот запущен в отдельном потоке")
    
    # VK бот запускаем в основном потоке
    try:
        logger.info("Запуск VK бота в основном потоке...")
        run_vk_bot()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершаем работу...")
    except Exception as e:
        logger.error(f"Ошибка в VK боте: {e}", exc_info=True)
    finally:
        logger.info("Оба бота остановлены")

if __name__ == '__main__':
    main()