from typing import Dict, Any

# In-memory conversation state
conversation_state: Dict[str, Dict[str, Any]] = {}

def update_state(user_id: str, key: str, value: Any) -> None:
    """Update conversation state for a user"""
    if user_id not in conversation_state:
        conversation_state[user_id] = {}
    conversation_state[user_id][key] = value

def get_state(user_id: str) -> Dict[str, Any]:
    """Get conversation state for a user"""
    return conversation_state.get(user_id, {})

def clear_state(user_id: str) -> None:
    """Clear conversation state for a user"""
    if user_id in conversation_state:
        del conversation_state[user_id]

def get_all_states() -> Dict[str, Dict[str, Any]]:
    """Get all conversation states"""
    return conversation_state