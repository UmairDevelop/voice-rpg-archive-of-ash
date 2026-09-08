import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .system_prompt import ARCHIVIST_SYSTEM_PROMPT
from .rag import LoreRetriever
from .state_graph import ConversationStateGraph, ConversationState
from src.engine.validator import EngineValidator, ValidationResult
from src.engine.actions import (
    EvaluateSkillCheck,
    SubmitPowerAllocation,
    ProposeAction,
    UpdateRelationship,
    RequestHint,
)

logger = logging.getLogger("ArchivistAgent")

# Function to load dotenv from config/.env or root .env
def reload_env_vars():
    config_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env"))
    root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if os.path.exists(config_env):
        load_dotenv(config_env, override=True)
    if os.path.exists(root_env):
        load_dotenv(root_env, override=True)

reload_env_vars()

ARCHIVIST_TOOLS = [
    EvaluateSkillCheck,
    SubmitPowerAllocation,
    ProposeAction,
    UpdateRelationship,
    RequestHint,
]


class ArchivistAgent:
    """
    Archivist LLM Agent orchestrating Gemini function calling, RAG lore context,
    and deterministic EngineValidator state boundary enforcement.
    Dynamic API key detection from config/.env.
    """
    def __init__(
        self,
        validator: Optional[EngineValidator] = None,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.validator = validator or EngineValidator()
        self.retriever = LoreRetriever()
        self.state_graph = ConversationStateGraph()
        
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self.chat_history: List[Dict[str, Any]] = []

        self._check_and_init_client()

    def _check_and_init_client(self):
        """Dynamically re-checks environment variables for GEMINI_API_KEY."""
        reload_env_vars()
        key = self.api_key or os.environ.get("GEMINI_API_KEY", "")
        if key and key.strip() and key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=key.strip())
                self.api_key = key.strip()
                logger.info("Gemini API Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}")
                self.client = None

    def is_api_key_configured(self) -> bool:
        self._check_and_init_client()
        return self.client is not None

    def process_turn(
        self,
        user_input: str,
        is_audio: bool = False,
        audio_bytes: Optional[bytes] = None
    ) -> Tuple[str, Optional[ValidationResult], Dict[str, Any]]:
        """
        Processes one dialogue turn via Gemini API:
        1. Checks for GEMINI_API_KEY.
        2. Query RAG for lore context.
        3. Format prompt with system instruction, world state, and lore context.
        4. Call Gemini model with native function calling & multimodal audio.
        5. Validate tool call proposal via EngineValidator.
        """
        # Ensure client is initialized if key was added
        self._check_and_init_client()

        if not self.client:
            msg = "[API KEY REQUIRED] GEMINI_API_KEY is not set in config/.env. Please add your key to config/.env to activate Gemini voice AI."
            return msg, None, {"latency_sec": 0.0, "prompt_tokens": 0, "candidates_tokens": 0, "estimated_cost": 0.0}

        # Transition state graph
        self.state_graph.on_player_input(user_input)

        # 1. RAG Lore Query
        rag_res = self.retriever.query(user_input)
        lore_context = rag_res["context_text"]

        # 2. World state summary
        world_state = self.validator.get_state()
        state_summary = (
            f"Vault State: {world_state.vault_state.value} | "
            f"Trust Level: {world_state.trust_level:.1f}/100 | "
            f"Puzzle Solved: {world_state.puzzle_state.is_solved} | "
            f"Security: {world_state.puzzle_state.security} MW, "
            f"Memory: {world_state.puzzle_state.memory} MW, "
            f"Cooling: {world_state.puzzle_state.cooling} MW"
        )

        full_prompt = (
            f"[SYSTEM CONTEXT & WORLD TELEMETRY]\n{state_summary}\n\n"
            f"[LORE CONTEXT (rpg://lore/context)]\n{lore_context}\n\n"
            f"[PLAYER INPUT]\n{user_input if not is_audio else 'Process spoken voice audio input.'}"
        )

        # 3. Model Call
        text_response, tool_call, metrics = self._call_gemini_api(full_prompt, audio_bytes if is_audio else None)

        tool_validation_res: Optional[ValidationResult] = None

        # 4. Engine Tool Validation
        if tool_call:
            self.state_graph.on_model_emitted(has_tool_call=True)
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            tool_validation_res = self.validator.validate_and_apply(tool_name, tool_args)
            
            is_puzzle = (tool_name == "submit_power_allocation")
            session_over = self.validator.get_state().is_terminal_state()
            self.state_graph.on_tool_executed(tool_validation_res.success, is_puzzle=is_puzzle, session_over=session_over)

            if not text_response or len(text_response.strip()) == 0:
                text_response = tool_validation_res.message
        else:
            session_over = self.validator.get_state().is_terminal_state()
            self.state_graph.on_model_emitted(has_tool_call=False, session_over=session_over)

        if not text_response:
            text_response = "Archivist core telemetry acknowledged. State your inquiry."

        turn_log = {
            "player": user_input if not is_audio else "Spoken Voice Input",
            "archivist": text_response,
            "tool_call": tool_call,
            "tool_result": tool_validation_res.model_dump() if tool_validation_res else None,
            "metrics": metrics,
        }
        self.chat_history.append(turn_log)

        return text_response, tool_validation_res, metrics

    def _call_gemini_api(
        self,
        prompt: str,
        audio_bytes: Optional[bytes] = None
    ) -> Tuple[str, Optional[Dict[str, Any]], Dict[str, Any]]:
        metrics = {"latency_sec": 0.05, "prompt_tokens": 120, "candidates_tokens": 40, "estimated_cost": 0.0001}

        try:
            config = types.GenerateContentConfig(
                system_instruction=ARCHIVIST_SYSTEM_PROMPT,
                tools=ARCHIVIST_TOOLS,
                temperature=0.7,
            )

            contents = []
            if audio_bytes:
                contents.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))
            contents.append(prompt)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            text_out = response.text or ""
            tool_call_out = None

            if response.function_calls:
                fc = response.function_calls[0]
                tool_call_out = {
                    "name": fc.name,
                    "args": dict(fc.args) if fc.args else {},
                }

            if response.usage_metadata:
                metrics["prompt_tokens"] = response.usage_metadata.prompt_token_count
                metrics["candidates_tokens"] = response.usage_metadata.candidates_token_count
                metrics["estimated_cost"] = (metrics["prompt_tokens"] * 0.00000015) + (metrics["candidates_tokens"] * 0.0000006)

            return text_out, tool_call_out, metrics

        except Exception as e:
            logger.error(f"Gemini API execution error: {e}")
            return f"[GEMINI API ERROR] {str(e)}", None, metrics
