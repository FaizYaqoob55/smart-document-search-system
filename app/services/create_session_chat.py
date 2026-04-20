import redis
import json
import uuid

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def create_session(document_ids: list[int] | None = None):
    session_id = str(uuid.uuid4())
    data = {"history": []}
    if document_ids is not None:
        data["document_ids"] = document_ids
    r.set(f"session:{session_id}", json.dumps(data), ex=86400)  # 24 hours
    return session_id


def load_session(session_id):
    raw = r.get(f"session:{session_id}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def get_history(session_id):
    data = load_session(session_id)
    if data is None:
        return []
    if isinstance(data, dict):
        return data.get("history", [])
    return data


def save_session(session_id, data): 
    r.set(f"session:{session_id}", json.dumps(data), ex=86400)
    return data


def save_message(session_id, role, content):
    data = load_session(session_id)
    if data is None:
        data = {"history": []}
    if isinstance(data, list):
        history = data
        data = {"history": history}
    else:
        history = data.get("history", [])

    history.append({"role": role, "content": content})
    history = history[-10:]
    data["history"] = history
    return save_session(session_id, data)



