import os
import redis
import logging
import database
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          filters, ConversationHandler, ContextTypes)

CHOOSING, ANSWERING = range(2)

logger = logging.getLogger(__name__)


def get_main_keyboard():
    buttons = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для викторины. Нажми «Новый вопрос», чтобы начать.",
        reply_markup=get_main_keyboard()
    )
    return CHOOSING


async def handle_new_question_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    redis_conn = context.application.bot_data['redis']
    user_id = update.effective_user.id
    question = database.get_random_question(redis_conn)

    if not question:
        await update.message.reply_text(
            "В базе нет вопросов. Запустите parser.py"
        )
        return CHOOSING

    state = database.get_user_state(redis_conn, user_id)
    state["current_question"] = question
    database.set_user_state(redis_conn, user_id, state)
    await update.message.reply_text(question['question'])
    return ANSWERING


async def handle_solution_attempt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    redis_conn = context.application.bot_data['redis']
    user_id = update.effective_user.id
    state = database.get_user_state(redis_conn, user_id)
    active_question = state.get("current_question")

    if not active_question:
        await update.message.reply_text("Нажмите «Новый вопрос».")
        return CHOOSING

    user_answer = update.message.text.strip().lower()
    raw_answer = active_question['answer']
    clean_answer = raw_answer.split('(')[0].split('.')[0]
    correct_answer = clean_answer.strip().lower()

    if user_answer == correct_answer:
        state["score"] = state.get("score", 0) + 1
        state["current_question"] = None
        database.set_user_state(redis_conn, user_id, state)
        await update.message.reply_text(
            "Правильно! Поздравляю! Для следующего "
            "вопроса нажми «Новый вопрос»",
            reply_markup=get_main_keyboard()
        )
        return CHOOSING

    await update.message.reply_text("Неправильно… Попробуешь ещё раз?")
    return ANSWERING


async def handle_surrender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_conn = context.application.bot_data['redis']
    user_id = update.effective_user.id
    state = database.get_user_state(redis_conn, user_id)

    current_q = state.get("current_question")
    if current_q:
        ans = current_q['answer']
        await update.message.reply_text(f"Правильный ответ: {ans}")

    return await handle_new_question_request(update, context)


async def handle_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    redis_conn = context.application.bot_data['redis']
    user_id = update.effective_user.id
    state = database.get_user_state(redis_conn, user_id)
    await update.message.reply_text(f"Ваш счёт: {state.get('score', 0)}")
    return CHOOSING


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    redis_conn = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=6379,
        decode_responses=True
    )

    token = os.getenv("TG_TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.bot_data['redis'] = redis_conn

    btn_filter = filters.Regex('^(Новый вопрос|Мой счёт|Сдаться)$')
    text_filter = filters.TEXT & ~filters.COMMAND & ~btn_filter

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex('^Новый вопрос$'),
                    handle_new_question_request
                ),
                MessageHandler(filters.Regex('^Мой счёт$'), handle_score),
            ],
            ANSWERING: [
                MessageHandler(filters.Regex('^Мой счёт$'), handle_score),
                MessageHandler(filters.Regex('^Сдаться$'), handle_surrender),
                MessageHandler(text_filter, handle_solution_attempt)
            ],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    logger.info("TG бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
