import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from .config import VK_TOKEN, VK_GROUP_ID
from . import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("VK бот запускается...")
    
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    
    logger.info("VK бот запущен и ожидает сообщений")
    
    for event in longpoll.listen():
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                message_text = event.text.strip()
                
                logger.info(f"Получено сообщение от {user_id}: {message_text}")
                
                handlers.handle_message(user_id, message_text, vk)
                
        except Exception as e:
            logger.error(f"Ошибка обработки события: {e}")

if __name__ == '__main__':
    main()