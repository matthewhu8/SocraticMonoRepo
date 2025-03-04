from typing import Dict
import time

class StudentSession:
    def __init__(self, problem_id: int):
        self.problem_id = problem_id
        self.revealed_values = set()
        self.formula_revealed = False
        self.hint_level = 0
        self.conversation_history = []
        self.attempt_count = 0
        self.last_interaction_time = time.time()
    
    def add_interaction(self, query: str, response: str):
        self.conversation_history.append({
            "role": "student",
            "content": query,
            "timestamp": time.time()
        })
        self.conversation_history.append({
            "role": "tutor",
            "content": response,
            "timestamp": time.time()
        })
        self.last_interaction_time = time.time()
        self.attempt_count += 1
    
    def reveal_value(self, key: str):
        self.revealed_values.add(key)
    
    def reveal_formula(self):
        self.formula_revealed = True
    
    def increase_hint_level(self):
        self.hint_level = min(5, self.hint_level + 1)
    
    def to_dict(self):
        return {
            "problem_id": self.problem_id,
            "revealed_values": list(self.revealed_values),
            "formula_revealed": self.formula_revealed,
            "hint_level": self.hint_level,
            "attempt_count": self.attempt_count,
            "last_interaction_time": self.last_interaction_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        session = cls(data["problem_id"])
        session.revealed_values = set(data.get("revealed_values", []))
        session.formula_revealed = data.get("formula_revealed", False)
        session.hint_level = data.get("hint_level", 0)
        session.attempt_count = data.get("attempt_count", 0)
        session.last_interaction_time = data.get("last_interaction_time", time.time())
        session.conversation_history = data.get("conversation_history", [])
        return session