import threading
import logging
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'tg_bot'))
sys.path.append(os.path.join(project_root, 'vk_bot'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def run_telegram_bot():
    import sys
    import os
    sys.path.append(os.path.join(project_root, 'tg_bot'))
    from tg_bot.main import main as telegram_main
    telegram_main()


def run_vk_bot():
    import sys
    import os
    sys.path.append(os.path.join(project_root, 'vk_bot'))
    from vk_bot.main import main as vk_main
    vk_main()


def main():
    logger = logging.getLogger(__name__)
    logger.info("Запуск обоих ботов...")
    vk_thread = threading.Thread(
        target=run_vk_bot,
        name="VKBotThread"
    )
    vk_thread.daemon = True
    vk_thread.start()
    logger.info("VK бот запущен в отдельном потоке")

    try:
        logger.info("Запуск Telegram бота в основном потоке...")
        run_telegram_bot()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершаем работу...")
    except Exception as e:
        logger.error(f"Ошибка в Telegram боте: {e}", exc_info=True)
    finally:
        logger.info("Оба бота остановлены")


if __name__ == '__main__':
    main()
