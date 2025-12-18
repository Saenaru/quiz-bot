import json
import random

def get_user_state(redis_conn, user_id):
    state = redis_conn.get(f"user:{user_id}")
    if state:
        data = json.loads(state)
        if "score" not in data: data["score"] = 0
        if "current_question" not in data: data["current_question"] = None
        return data
    return {"current_question": None, "score": 0}

def set_user_state(redis_conn, user_id, state):
    redis_conn.set(f"user:{user_id}", json.dumps(state))

def get_random_question(redis_conn):
    count = redis_conn.hlen("questions")
    if count == 0:
        return None
    random_index = random.randint(0, count - 1)
    question_json = redis_conn.hget("questions", f"q:{random_index}")
    return json.loads(question_json)
