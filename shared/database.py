import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

def get_connection():
    db_file = None
    db_file = os.getenv('DB_FILE')

    if not db_file:
        db_file = 'quiz_bot.db'

    if not os.path.isabs(db_file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        possible_locations = [
            os.path.join(project_root, db_file),
            os.path.join(current_dir, db_file),
            db_file
        ]
        for location in possible_locations:
            if os.path.exists(location):
                db_file = location
                break
    logger.info(f"Используется база данных: {db_file}")
    return sqlite3.connect(db_file)

def get_or_create_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT user_id, score, correct_answers, total_questions, current_question_id 
    FROM user_stats WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    if result:
        user_data = {
            'user_id': result[0],
            'score': result[1],
            'correct_answers': result[2],
            'total_questions': result[3],
            'current_question_id': result[4],
        }
    else:
        cursor.execute('''
        INSERT INTO user_stats (user_id, score, correct_answers, total_questions)
        VALUES (?, 0, 0, 0)
        ''', (user_id,))
        conn.commit()
        user_data = {
            'user_id': user_id,
            'score': 0,
            'correct_answers': 0,
            'total_questions': 0,
            'current_question_id': None,
        }
    conn.close()
    return user_data

def update_user(user_id, username=None, first_name=None, last_name=None, 
               score=None, correct_answers=None, total_questions=None, current_question_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT username, first_name, last_name, score, correct_answers, total_questions, current_question_id
    FROM user_stats WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    
    if result:
        current_username = username if username is not None else result[0]
        current_first_name = first_name if first_name is not None else result[1]
        current_last_name = last_name if last_name is not None else result[2]
        current_score = score if score is not None else result[3]
        current_correct = correct_answers if correct_answers is not None else result[4]
        current_total = total_questions if total_questions is not None else result[5]
        current_qid = current_question_id if current_question_id is not None else result[6]
    else:
        current_username = username
        current_first_name = first_name
        current_last_name = last_name
        current_score = score if score is not None else 0
        current_correct = correct_answers if correct_answers is not None else 0
        current_total = total_questions if total_questions is not None else 0
        current_qid = current_question_id
    cursor.execute('''
    INSERT OR REPLACE INTO user_stats 
    (user_id, username, first_name, last_name, score, correct_answers, total_questions, 
     current_question_id, question_assigned_at, last_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 
            CASE WHEN ? IS NOT NULL THEN CURRENT_TIMESTAMP ELSE NULL END, 
            CURRENT_TIMESTAMP)
    ''', (user_id, current_username, current_first_name, current_last_name, 
          current_score, current_correct, current_total, current_qid, current_qid))
    conn.commit()
    conn.close()

def save_answer_history(user_id, question_id, user_answer, is_correct):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO question_history (user_id, question_id, user_answer, is_correct)
    VALUES (?, ?, ?, ?)
    ''', (user_id, question_id, user_answer, is_correct))
    conn.commit()
    conn.close()

def get_random_question(user_id, exclude_current=True):
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_current:
        cursor.execute('''
        SELECT q.question_id, q.question_text, q.answer_text 
        FROM questions q
        WHERE NOT EXISTS (
            SELECT 1 FROM question_history qh 
            WHERE qh.question_id = q.question_id AND qh.user_id = ?
        )
        ORDER BY RANDOM() LIMIT 1
        ''', (user_id,))
    else:
        cursor.execute('''
        SELECT q.question_id, q.question_text, q.answer_text 
        FROM questions q
        WHERE q.question_id NOT IN (
            SELECT current_question_id FROM user_stats WHERE user_id = ?
        )
        AND NOT EXISTS (
            SELECT 1 FROM question_history qh 
            WHERE qh.question_id = q.question_id AND qh.user_id = ?
        )
        ORDER BY RANDOM() LIMIT 1
        ''', (user_id, user_id))
    result = cursor.fetchone()
    if not result:
        cursor.execute('''
        SELECT question_id, question_text, answer_text FROM questions 
        WHERE question_id NOT IN (
            SELECT current_question_id FROM user_stats WHERE user_id = ?
        )
        ORDER BY RANDOM() LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
    if not result:
        cursor.execute('''
        SELECT question_id, question_text, answer_text FROM questions 
        ORDER BY RANDOM() LIMIT 1
        ''')
        result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'id': result[0],
            'question': result[1],
            'answer': result[2]
        }
    return None

def get_current_question(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT q.question_id, q.question_text, q.answer_text
    FROM user_stats u
    LEFT JOIN questions q ON u.current_question_id = q.question_id
    WHERE u.user_id = ? AND u.current_question_id IS NOT NULL
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'id': result[0],
            'question': result[1],
            'answer': result[2]
        }
    return None

def clear_current_question(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE user_stats 
    SET current_question_id = NULL, question_assigned_at = NULL
    WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def get_question_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions')
    count = cursor.fetchone()[0]
    conn.close()
    return count
