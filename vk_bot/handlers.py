import logging
from shared import database as db
from keyboards import get_main_keyboard

logger = logging.getLogger(__name__)

def handle_message(user_id, message_text, vk):
    
    user_data = db.get_or_create_user(user_id)
    
    if message_text.lower() == 'начать' or message_text.lower() == '/start' or message_text.lower() == 'start':
        return start_handler(user_id, vk)
    
    elif message_text == 'Новый вопрос':
        return new_question_handler(user_id, vk)
    
    elif message_text == 'Сдаться':
        return give_up_handler(user_id, vk)
    
    elif message_text == 'Мой счёт':
        return show_score_handler(user_id, vk)
    
    elif message_text.lower() == 'помощь' or message_text.lower() == '/help' or message_text.lower() == 'help':
        return help_handler(user_id, vk)
    
    else:
        return check_answer_handler(user_id, message_text, vk)

def start_handler(user_id, vk):
    
    question_count = db.get_question_count()
    
    if question_count == 0:
        send_message(
            vk, user_id,
            "В базе данных нет вопросов.\n"
            "Запустите сначала parse_questions.py для загрузки вопросов.",
            get_main_keyboard()
        )
        return
    
    current_question = db.get_current_question(user_id)
    
    if current_question:
        send_message(
            vk, user_id,
            f"Привет!\nВ базе {question_count} вопросов.\n\n"
            "У вас есть неотвеченный вопрос. Напишите ответ в чат или нажмите 'Сдаться'.",
            get_main_keyboard()
        )
    else:
        send_message(
            vk, user_id,
            f"Привет!\nЯ бот для викторины. В базе {question_count} вопросов.\n\n"
            "Как играть:\n"
            "• 'Новый вопрос' - получить случайный вопрос\n"
            "• Напиши ответ в чат\n"
            "• 'Сдаться' - показать правильный ответ и получить новый вопрос\n"
            "• 'Мой счёт' - твоя статистика\n\n"
            "Ответы не чувствительны к регистру.",
            get_main_keyboard()
        )

def new_question_handler(user_id, vk):    
    question_data = db.get_random_question(user_id)
    
    if not question_data:
        send_message(
            vk, user_id,
            "Не удалось получить вопрос. База данных пуста.",
            get_main_keyboard()
        )
        return
    
    db.update_user(
        user_id=user_id,
        current_question_id=question_data['id']
    )
    
    logger.info(f"Пользователю {user_id} задан вопрос ID: {question_data['id']}")
    
    send_message(
        vk, user_id,
        f"Вопрос:\n\n{question_data['question']}",
        get_main_keyboard()
    )

def give_up_handler(user_id, vk):    
    current_question = db.get_current_question(user_id)
    
    if not current_question:
        send_message(
            vk, user_id,
            "Сначала получите вопрос, нажав 'Новый вопрос'",
            get_main_keyboard()
        )
        return
    
    db.save_answer_history(
        user_id=user_id,
        question_id=current_question['id'],
        user_answer="[сдался]",
        is_correct=False
    )
    
    user_data = db.get_or_create_user(user_id)
    user_data['total_questions'] += 1
    
    db.update_user(
        user_id=user_id,
        total_questions=user_data['total_questions'],
        current_question_id=None
    )
    
    send_message(
        vk, user_id,
        f"Правильный ответ:\n\n{current_question['answer']}",
        get_main_keyboard()
    )
    
    new_question_data = db.get_random_question(user_id)
    
    if not new_question_data:
        send_message(
            vk, user_id,
            "Не удалось получить новый вопрос. База данных пуста.",
            get_main_keyboard()
        )
        return
    
    db.update_user(
        user_id=user_id,
        current_question_id=new_question_data['id']
    )
    
    logger.info(f"Пользователю {user_id} задан новый вопрос ID: {new_question_data['id']}")
    
    send_message(
        vk, user_id,
        f"Следующий вопрос:\n\n{new_question_data['question']}",
        get_main_keyboard()
    )

def show_score_handler(user_id, vk):    
    user_data = db.get_or_create_user(user_id)
    
    score = user_data['score']
    total_questions = user_data['total_questions']
    correct_answers = user_data['correct_answers']
    
    current_question = db.get_current_question(user_id)
    
    stats_text = "Ваша статистика:\n\n"
    
    if total_questions == 0:
        stats_text += "Вы еще не ответили ни на один вопрос.\n"
    else:
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        stats_text += f"Правильных ответов: {correct_answers}\n"
        stats_text += f"Неправильных: {total_questions - correct_answers}\n"
        stats_text += f"Всего вопросов: {total_questions}\n"
        stats_text += f"Точность: {accuracy:.1f}%\n"
        stats_text += f"Очки: {score}\n\n"
    
    if current_question:
        stats_text += "У вас есть активный вопрос. Напишите ответ в чат или нажмите 'Сдаться'.\n"
    
    send_message(vk, user_id, stats_text, get_main_keyboard())

def check_answer_handler(user_id, user_answer, vk):    
    question_data = db.get_current_question(user_id)
    
    if not question_data:
        send_message(
            vk, user_id,
            "Нажмите 'Новый вопрос' чтобы получить вопрос",
            get_main_keyboard()
        )
        return
    
    def normalize_text(text):
        text = text.lower().strip()
        text = ' '.join(text.split())
        for char in '.,!?;:"\'()[]{}':
            text = text.replace(char, '')
        return text
    
    normalized_user = normalize_text(user_answer)
    normalized_correct = normalize_text(question_data['answer'])
    
    is_correct = normalized_user == normalized_correct
    
    user_data = db.get_or_create_user(user_id)
    
    user_data['total_questions'] += 1
    if is_correct:
        user_data['score'] += 1
        user_data['correct_answers'] += 1
    
    db.save_answer_history(
        user_id=user_id,
        question_id=question_data['id'],
        user_answer=user_answer,
        is_correct=is_correct
    )
    
    db.update_user(
        user_id=user_id,
        score=user_data['score'],
        correct_answers=user_data['correct_answers'],
        total_questions=user_data['total_questions'],
        current_question_id=None
    )
    
    if is_correct:
        response = "Правильно! Поздравляю!\n"
        response += "Для следующего вопроса нажми «Новый вопрос»"
    else:
        response = "Неправильно… Попробуешь ещё раз?\n"
        response += f"Правильный ответ: {question_data['answer']}"
    
    send_message(vk, user_id, response, get_main_keyboard())

def help_handler(user_id, vk):    
    help_text = (
        "Как играть:\n\n"
        "• 'Новый вопрос' - случайный вопрос\n"
        "• 'Сдаться' - показать правильный ответ и получить новый вопрос\n"
        "• 'Мой счёт' - ваша статистика\n"
        "• 'Начать' - начать сначала\n"
        "• 'Помощь' - эта справка\n\n"
        "Ответы не чувствительны к регистру."
    )
    
    send_message(vk, user_id, help_text, get_main_keyboard())

def send_message(vk, user_id, message, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            keyboard=keyboard,
            random_id=0
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")