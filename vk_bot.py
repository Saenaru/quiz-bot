import os
import redis
import vk_api
import random
import database
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def main():
    load_dotenv()
    vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
    vk = vk_session.get_api()
    redis_conn = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)

    for event in VkLongPoll(vk_session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            state = database.get_user_state(redis_conn, user_id)
            text = event.text.strip()
            rid = random.randint(1, 1000000)

            if text == "Новый вопрос":
                q = database.get_random_question(redis_conn)
                state["current_question"] = q
                database.set_user_state(redis_conn, user_id, state)
                vk.messages.send(user_id=user_id, message=q['question'], keyboard=get_main_keyboard(), random_id=rid)
            elif text == "Сдаться":
                q_old = state.get("current_question")
                if q_old:
                    vk.messages.send(user_id=user_id, message=f"Ответ был: {q_old['answer']}", random_id=rid)
                q = database.get_random_question(redis_conn)
                state["current_question"] = q
                database.set_user_state(redis_conn, user_id, state)
                vk.messages.send(user_id=user_id, message=f"Следующий вопрос:\n{q['question']}", random_id=random.randint(1, 1000000))

            elif text == "Мой счёт":
                vk.messages.send(user_id=user_id, message=f"Ваш счёт: {state.get('score', 0)}", random_id=rid)

            else:
                q = state.get("current_question")
                if not q:
                    vk.messages.send(user_id=user_id, message="Нажми «Новый вопрос».", random_id=rid)
                elif text.lower() == q['answer'].split('(')[0].split('.')[0].strip().lower():
                    state["score"] = state.get("score", 0) + 1
                    state["current_question"] = None
                    database.set_user_state(redis_conn, user_id, state)
                    vk.messages.send(user_id=user_id, message="Правильно!", random_id=rid)
                else:
                    vk.messages.send(user_id=user_id, message="Неправильно...", random_id=rid)

if __name__ == "__main__":
    main()
