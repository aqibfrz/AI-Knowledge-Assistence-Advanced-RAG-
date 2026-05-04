from collections import defaultdict
from typing import Dict, List, Tuple


class ChatMemoryStore:
    def __init__(self) -> None:
        self._store: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    def add_turn(self, session_id: str, user: str, assistant: str) -> None:
        self._store[session_id].append((user, assistant))

    def get_context(self, session_id: str, max_turns: int = 4) -> str:
        turns = self._store.get(session_id, [])[-max_turns:]
        lines = []
        for user, assistant in turns:
            lines.append(f"User: {user}")
            lines.append(f"Assistant: {assistant}")
        return "\n".join(lines)

    def session_count(self) -> int:
        return len(self._store)
