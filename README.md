# Quiz Bot

Бот для проведения викторин с вопросами из текстовых файлов. Пользователи могут получать случайные вопросы, отвечать на них и отслеживать свою статистику.

## 1. Клонирование и установка зависимостей
```sh
# Клонировать репозиторий
git clone <repository-url>
cd quiz-bot

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Для Windows:
venv\Scripts\activate
# Для Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## 2. Настройка переменных окружения
```sh
# Создать файл .env на основе примера
cp .env.example .env

# Отредактировать .env файл, добавив токен бота
TELEGRAM_TOKEN=ваш_токен_бота
DB_FILE=quiz_bot.db
```

## Запуск бота
```sh
python main.py
```