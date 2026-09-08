from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SkillType(str, Enum):
    PERSUASION = "persuasion"
    INTIMIDATION = "intimidation"
    INSIGHT = "insight"


class ActionType(str, Enum):
    ALLOW_ACCESS = "ALLOW_ACCESS"
    DENY_ACCESS = "DENY_ACCESS"
    REVEAL_CLUE = "REVEAL_CLUE"
    OFFER_HINT = "OFFER_HINT"
    OFFER_TRADEOFF = "OFFER_TRADEOFF"
    ASSIGN_RESTORATION_TASK = "ASSIGN_RESTORATION_TASK"
    UPDATE_RELATIONSHIP = "UPDATE_RELATIONSHIP"
    LOCK_SUBSYSTEM = "LOCK_SUBSYSTEM"
    END_CONVERSATION = "END_CONVERSATION"


class EvaluateSkillCheck(BaseModel):
    """Evaluate a skill check against a target difficulty class (DC)."""
    skillType: SkillType = Field(..., description="The type of skill check being performed.")
    targetDC: float = Field(..., description="The Target Difficulty Class (DC) to meet or exceed.")


class SubmitPowerAllocation(BaseModel):
    """Submit a power allocation proposal for security, memory, and cooling subsystems."""
    security: float = Field(..., description="Megawatts allocated to Security subsystem.")
    memory: float = Field(..., description="Megawatts allocated to Memory/Schematic subsystem.")
    cooling: float = Field(..., description="Megawatts allocated to Thermal Cooling subsystem.")


class ProposeAction(BaseModel):
    """Propose a high-level game state change action."""
    actionType: ActionType = Field(..., description="The state transition action type.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary payload parameters for the action.")


class UpdateRelationship(BaseModel):
    """Update Archivist's trust and relationship metric with the player."""
    delta: float = Field(..., description="Numerical change in trust level (-100 to +100).")
    reason: str = Field(..., description="Reason for the trust level update.")


class RequestHint(BaseModel):
    """Request a staged hint regarding the power puzzle or archive access."""
    level: int = Field(..., description="Hint level (1: gentle nudge, 2: directional clue, 3: explicit constraint hint).")
