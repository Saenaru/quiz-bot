import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from keyboards import get_main_keyboard
import database as db

logger = logging.getLogger(__name__)

WAITING_FOR_ANSWER = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    question_count = db.get_question_count()
    
    if question_count == 0:
        await update.message.reply_text(
            "В базе данных нет вопросов.\n"
            "Запустите сначала parse_questions.py для загрузки вопросов.",
            reply_markup=get_main_keyboard()
        )
        return
    
    logger.info(f"Пользователь {user.first_name} (ID: {user.id}) запустил бота")
    
    db.update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    current_question = db.get_current_question(user.id)
    if current_question:
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n"
            f"В базе {question_count} вопросов.\n\n"
            "У вас есть неотвеченный вопрос. Напишите ответ в чат или нажмите 'Сдаться'.",
            reply_markup=get_main_keyboard()
        )
        return WAITING_FOR_ANSWER
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n"
            f"Я бот для викторины. В базе {question_count} вопросов.\n\n"
            "Как играть:\n"
            "• 'Новый вопрос' - получить случайный вопрос\n"
            "• Напиши ответ в чат\n"
            "• 'Сдаться' - показать правильный ответ и получить новый вопрос\n"
            "• 'Мой счёт' - твоя статистика\n\n"
            "Ответы не чувствительны к регистру.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def new_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    question_data = db.get_random_question(user.id)
    
    if not question_data:
        await update.message.reply_text(
            "Не удалось получить вопрос. База данных пуста.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    db.update_user(
        user_id=user.id,
        current_question_id=question_data['id']
    )
    
    logger.info(f"Пользователю {user.first_name} задан вопрос ID: {question_data['id']}")
    
    await update.message.reply_text(
        f"Вопрос:\n\n{question_data['question']}",
        reply_markup=get_main_keyboard()
    )
    
    return WAITING_FOR_ANSWER

async def give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    current_question = db.get_current_question(user.id)
    
    if not current_question:
        await update.message.reply_text(
            "Сначала получите вопрос, нажав 'Новый вопрос'",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    db.save_answer_history(
        user_id=user.id,
        question_id=current_question['id'],
        user_answer="[сдался]",
        is_correct=False
    )
    
    user_data = db.get_or_create_user(user.id)
    user_data['total_questions'] += 1
    
    db.update_user(
        user_id=user.id,
        total_questions=user_data['total_questions'],
        current_question_id=None
    )
    
    await update.message.reply_text(
        f"Правильный ответ:\n\n{current_question['answer']}"
    )
    
    new_question_data = db.get_random_question(user.id)
    
    if not new_question_data:
        await update.message.reply_text(
            "Не удалось получить новый вопрос. База данных пуста.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    db.update_user(
        user_id=user.id,
        current_question_id=new_question_data['id']
    )
    
    logger.info(f"Пользователю {user.first_name} задан новый вопрос ID: {new_question_data['id']}")
    await update.message.reply_text(
        f"Следующий вопрос:\n\n{new_question_data['question']}",
        reply_markup=get_main_keyboard()
    )
    
    return WAITING_FOR_ANSWER

async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = db.get_or_create_user(user.id)
    
    score = user_data['score']
    total_questions = user_data['total_questions']
    correct_answers = user_data['correct_answers']
    
    current_question = db.get_current_question(user.id)
    
    stats_text = f"Ваша статистика:\n\n"
    
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
    
    await update.message.reply_text(stats_text, reply_markup=get_main_keyboard())
    
    if current_question:
        return WAITING_FOR_ANSWER
    
    return ConversationHandler.END

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    question_data = db.get_current_question(user.id)
    
    if not question_data:
        await update.message.reply_text(
            "Нажмите 'Новый вопрос' чтобы получить вопрос",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    user_answer = update.message.text.strip()
    
    def normalize_text(text):
        text = text.lower().strip()
        text = ' '.join(text.split())
        for char in '.,!?;:"\'()[]{}':
            text = text.replace(char, '')
        return text
    
    normalized_user = normalize_text(user_answer)
    normalized_correct = normalize_text(question_data['answer'])
    
    is_correct = normalized_user == normalized_correct
    
    user_data = db.get_or_create_user(user.id)
    
    user_data['total_questions'] += 1
    if is_correct:
        user_data['score'] += 1
        user_data['correct_answers'] += 1
    
    db.save_answer_history(
        user_id=user.id,
        question_id=question_data['id'],
        user_answer=user_answer,
        is_correct=is_correct
    )
    
    db.update_user(
        user_id=user.id,
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
    
    await update.message.reply_text(
        response,
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как играть:\n\n"
        "• 'Новый вопрос' - случайный вопрос\n"
        "• 'Сдаться' - показать правильный ответ и получить новый вопрос\n"
        "• 'Мой счёт' - ваша статистика\n"
        "• /start - начать сначала\n"
        "• /help - эта справка\n\n"
        "Ответы не чувствительны к регистру.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    db.clear_current_question(user.id)
    
    await update.message.reply_text(
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

def get_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Новый вопрос$'), new_question),
            MessageHandler(filters.Regex('^Сдаться$'), give_up),
            MessageHandler(filters.Regex('^Мой счёт$'), show_score),
        ],
        states={
            WAITING_FOR_ANSWER: [
                MessageHandler(filters.Regex('^Новый вопрос$'), new_question),
                MessageHandler(filters.Regex('^Сдаться$'), give_up),
                MessageHandler(filters.Regex('^Мой счёт$'), show_score),
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('help', help_command),
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Новый вопрос$'), new_question),
            MessageHandler(filters.Regex('^Сдаться$'), give_up),
            MessageHandler(filters.Regex('^Мой счёт$'), show_score),
        ],
        allow_reentry=True
    )