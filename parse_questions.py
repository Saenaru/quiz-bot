import os
import re
import json
import sqlite3
import glob
from pathlib import Path

def create_database():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT UNIQUE,
        question_text TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        source_file TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        score INTEGER DEFAULT 0,
        correct_answers INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0,
        current_question_id TEXT,
        question_assigned_at TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_question_id) REFERENCES questions (question_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id TEXT,
        user_answer TEXT,
        is_correct BOOLEAN,
        answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_stats (user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def parse_questions_from_text(content):
    questions = []
    
    question_pattern = r'Вопрос\s+\d+:'
    question_sections = re.split(question_pattern, content, flags=re.IGNORECASE)
    
    for i, section in enumerate(question_sections[1:], 1):
        answer_match = None
        
        patterns = [
            r'Ответ[\.:]?\s*(.*?)(?=\n\s*(?:Автор:|Комментарий:|Источник:|Зачет:|$))',
            r'Ответ[\.:]?\s*(.*?)(?=\n\n)',
            r'Ответ[\.:]?\s*(.*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, section, re.DOTALL)
            if match:
                answer_match = match
                break
        
        if answer_match:
            question_text = section[:answer_match.start()].strip()
            answer_text = answer_match.group(1).strip()
            
            question_text = re.sub(r'\s+', ' ', question_text)
            question_text = re.sub(r'^\d+\.\s*', '', question_text)
            question_text = question_text.strip('"\' \n')
            
            answer_text = re.sub(r'\s+', ' ', answer_text)
            answer_text = answer_text.strip('"\' \n')
            
            if answer_text.endswith('.'):
                answer_text = answer_text[:-1]
            
            questions.append({
                'question': question_text,
                'answer': answer_text
            })
    
    return questions

def parse_file(file_path):
    try:
        for encoding in ['koi8-r', 'cp1251', 'utf-8', 'utf-8-sig']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            return []
        
        filename = os.path.basename(file_path)
        questions = parse_questions_from_text(content)
        
        return questions
    
    except Exception as e:
        return []

def save_questions_to_db(questions):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for i, q in enumerate(questions, 1):
        q_id = f"q_{i:04d}"
        
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO questions (question_id, question_text, answer_text, source_file)
            VALUES (?, ?, ?, ?)
            ''', (q_id, q['question'], q['answer'], q.get('source_file', 'unknown')))
            
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except sqlite3.IntegrityError:
            skipped += 1
    
    conn.commit()
    conn.close()
    
    return inserted, skipped

def get_stats_from_db():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT source_file) FROM questions')
    total_files = cursor.fetchone()[0]
    
    conn.close()
    
    return total_questions, total_files

def main():
    create_database()
    questions_dir = 'quiz-questions'
    if not os.path.exists(questions_dir):
        print(f"Папка '{questions_dir}' не найдена!")
        print(f"Создайте папку '{questions_dir}' и поместите туда файлы с вопросами")
        return

    txt_files = glob.glob(os.path.join(questions_dir, '*.txt'))
    
    if not txt_files:
        print(f"В папке '{questions_dir}' не найдено файлов .txt")
        return
    
    all_questions = []
    for txt_file in txt_files:
        questions = parse_file(txt_file)
        for q in questions:
            q['source_file'] = os.path.basename(txt_file)
        
        all_questions.extend(questions)
    
    if all_questions:
        inserted, skipped = save_questions_to_db(all_questions)
        return
    
    else:
        print("Не удалось найти ни одного вопроса")
        print("Проверьте формат файлов. Ожидается:")
        print("  Вопрос X: [текст вопроса]")
        print("  Ответ: [правильный ответ]")

if __name__ == "__main__":
    main()