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
    redis_conn = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=6379,
        decode_responses=True
    )

    for event in VkLongPoll(vk_session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            state = database.get_user_state(redis_conn, user_id)
            text = event.text.strip()
            rid = random.randint(1, 1000000)

            if text == "Новый вопрос":
                new_question = database.get_random_question(redis_conn)
                state["current_question"] = new_question
                database.set_user_state(redis_conn, user_id, state)
                vk.messages.send(
                    user_id=user_id,
                    message=new_question['question'],
                    keyboard=get_main_keyboard(),
                    random_id=rid
                )

            elif text == "Сдаться":
                previous_question = state.get("current_question")
                if previous_question:
                    answer_text = f"Ответ был: {previous_question['answer']}"
                    vk.messages.send(
                        user_id=user_id,
                        message=answer_text,
                        random_id=rid
                    )

                next_question = database.get_random_question(redis_conn)
                state["current_question"] = next_question
                database.set_user_state(redis_conn, user_id, state)

                msg = f"Следующий вопрос:\n{next_question['question']}"
                vk.messages.send(
                    user_id=user_id,
                    message=msg,
                    random_id=random.randint(1, 1000000)
                )

            elif text == "Мой счёт":
                score_msg = f"Ваш счёт: {state.get('score', 0)}"
                vk.messages.send(
                    user_id=user_id,
                    message=score_msg,
                    random_id=rid
                )

            else:
                unanswered_question = state.get("current_question")
                if not unanswered_question:
                    vk.messages.send(
                        user_id=user_id,
                        message="Нажми «Новый вопрос».",
                        random_id=rid
                    )
                    continue

                raw_answer = unanswered_question['answer']
                clean_answer = raw_answer.split('(')[0].split('.')[0]
                correct_answer = clean_answer.strip().lower()

                if text.lower() == correct_answer:
                    state["score"] = state.get("score", 0) + 1
                    state["current_question"] = None
                    database.set_user_state(redis_conn, user_id, state)
                    vk.messages.send(
                        user_id=user_id,
                        message="Правильно!",
                        random_id=rid
                    )
                else:
                    vk.messages.send(
                        user_id=user_id,
                        message="Неправильно...",
                        random_id=rid
                    )


if __name__ == "__main__":
    main()
