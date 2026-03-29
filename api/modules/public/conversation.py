# api/modules/public/conversation.py
from typing import Optional

# In-memory conversation store (for demo; production would use Redis or DB)
_conversations: dict[str, list[dict]] = {}

MAX_FOLLOW_UPS = 3


def get_conversation(conversation_id: str) -> list[dict]:
    """Get conversation history."""
    return _conversations.get(conversation_id, [])


def add_message(conversation_id: str, role: str, content: str):
    """Add a message to conversation history."""
    if conversation_id not in _conversations:
        _conversations[conversation_id] = []
    _conversations[conversation_id].append({"role": role, "content": content})


def conversation_length(conversation_id: str) -> int:
    """Get number of exchanges in a conversation."""
    history = _conversations.get(conversation_id, [])
    return len([m for m in history if m["role"] == "user"])


def clear_conversation(conversation_id: str):
    """Clear a conversation."""
    _conversations.pop(conversation_id, None)
