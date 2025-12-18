import os
import argparse
import redis
import json
from dotenv import load_dotenv

def parse_quiz_file(filepath):
    with open(filepath, 'r', encoding='KOI8-R', errors='ignore') as f:
        content = f.read()
    blocks = content.split('Вопрос ')
    questions = []
    for block in blocks[1:]:
        try:
            parts = block.split('Ответ:', 1)
            if len(parts) < 2: continue
            q_text = parts[0].split('\n', 1)[1].strip()
            a_text = parts[1].split('\nАвтор:', 1)[0].strip()
            questions.append({'question': q_text, 'answer': a_text})
        except (IndexError, ValueError):
            continue
    return questions

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description='Парсинг вопросов в Redis')
    parser.add_argument('--path', default='quiz-questions', help='Путь к папке с вопросами')
    args = parser.parse_args()

    redis_conn = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=os.getenv('REDIS_PORT', 6379),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )

    total = 0
    for filename in os.listdir(args.path):
        if filename.endswith(".txt"):
            questions = parse_quiz_file(os.path.join(args.path, filename))
            for q in questions:
                redis_conn.hset("questions", f"q:{total}", json.dumps(q))
                total += 1
    print(f"Успешно загружено {total} вопросов.")

if __name__ == "__main__":
    main()
