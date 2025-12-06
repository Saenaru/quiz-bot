from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['Новый вопрос', 'Сдаться'],
            ['Мой счёт']
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )