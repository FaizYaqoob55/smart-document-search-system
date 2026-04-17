import redis
import json
import uuid

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def create_session():
    session_id = str(uuid.uuid4())
    r.set(f"session:{session_id}", json.dumps([]), ex=86400)  # 24 hours
    return session_id


def get_history(session_id):
    data = r.get(f"session:{session_id}")
    return json.loads(data) if data else []


def save_message(session_id, role, content):
    history = get_history(session_id)

    history.append({"role": role, "content": content})

    # rolling window (last 10 messages)
    history = history[-10:]

    r.set(f"session:{session_id}", json.dumps(history), ex=86400)  #24 hours

    return history



