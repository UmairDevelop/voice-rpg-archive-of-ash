import logging
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StateGraph")


class ConversationState(str, Enum):
    IDLE_LISTENING = "IDLE_LISTENING"
    MODEL_GENERATING = "MODEL_GENERATING"
    AWAITING_TOOL_RESULT = "AWAITING_TOOL_RESULT"
    PUZZLE_ACTIVE = "PUZZLE_ACTIVE"
    SESSION_END = "SESSION_END"


class StateTransition(Dict[str, Any]):
    from_state: ConversationState
    to_state: ConversationState
    reason: str
    timestamp: float


class ConversationStateGraph:
    """
    Explicit Conversation State Machine for Archivist encounter.
    Logs every state transition and handles conditional routing edges.
    """
    def __init__(self, initial_state: ConversationState = ConversationState.IDLE_LISTENING):
        self.current_state = initial_state
        self.history: List[Dict[str, Any]] = []
        self._log_transition(None, initial_state, "Initialization")

    def transition_to(self, new_state: ConversationState, reason: str) -> ConversationState:
        old_state = self.current_state
        if old_state == new_state:
            return self.current_state

        self.current_state = new_state
        self._log_transition(old_state, new_state, reason)
        return self.current_state

    def _log_transition(self, old_state: Optional[ConversationState], new_state: ConversationState, reason: str):
        entry = {
            "from": old_state.value if old_state else "START",
            "to": new_state.value,
            "reason": reason,
        }
        self.history.append(entry)
        logger.info(f"[STATE GRAPH TRANSITION] {entry['from']} ──({reason})──> {entry['to']}")

    def on_player_input(self, text_or_audio: str) -> ConversationState:
        """Edge: Player input received -> transition to MODEL_GENERATING"""
        if self.current_state in [ConversationState.SESSION_END]:
            logger.warning("Player input received in SESSION_END state.")
            return self.current_state
        return self.transition_to(ConversationState.MODEL_GENERATING, f"Received player input: '{text_or_audio[:30]}...'")

    def on_model_emitted(self, has_tool_call: bool, is_puzzle: bool = False, session_over: bool = False) -> ConversationState:
        """Edge: Model output evaluated"""
        if session_over:
            return self.transition_to(ConversationState.SESSION_END, "Session ended by model decision or engine rule.")
        if has_tool_call:
            return self.transition_to(ConversationState.AWAITING_TOOL_RESULT, "Model proposed a structured tool call.")
        if is_puzzle:
            return self.transition_to(ConversationState.PUZZLE_ACTIVE, "Power puzzle console active.")
        return self.transition_to(ConversationState.IDLE_LISTENING, "Model generation complete, waiting for next player input.")

    def on_tool_executed(self, result_success: bool, is_puzzle: bool = False, session_over: bool = False) -> ConversationState:
        """Edge: Tool execution complete"""
        if session_over:
            return self.transition_to(ConversationState.SESSION_END, "Tool result concluded session.")
        if is_puzzle:
            return self.transition_to(ConversationState.PUZZLE_ACTIVE, "Puzzle interaction processed.")
        return self.transition_to(ConversationState.MODEL_GENERATING, "Tool result ready; returning to model synthesis.")
