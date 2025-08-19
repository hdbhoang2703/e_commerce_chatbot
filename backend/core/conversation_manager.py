from collections import defaultdict, deque

class ConversationManager:
    def __init__(self, system_prompt: str = "", maxlen:int = 10):
        self.system_prompt = system_prompt
        self.sessions = defaultdict(lambda: deque(maxlen=maxlen))

    def add_message(self, session_id: str, role: str, content: str):
        self.sessions[session_id].append({"role": role, "content": content})

    def get_messages(self, session_id):
        return [{"role": "system", "content": self.system_prompt}] + list(self.sessions.get(session_id, []))

    def clear_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

