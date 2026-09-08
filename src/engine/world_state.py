from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VaultDoorState(str, Enum):
    SEALED = "SEALED"
    CRACKED = "CRACKED"
    OPEN = "OPEN"


class PlayerState(BaseModel):
    x: float = 64.0
    y: float = 64.0
    facing: str = "down"  # up, down, left, right
    near_terminal: bool = False
    near_power_console: bool = False
    near_vault_door: bool = False
    near_archivist: bool = False
    idle_timer: float = 0.0


class PuzzleState(BaseModel):
    total_power: float = 100.0
    security: float = 50.0
    memory: float = 30.0
    cooling: float = 20.0
    is_solved: bool = False
    attempts: int = 0
    last_error: Optional[str] = None


class WorldState(BaseModel):
    vault_state: VaultDoorState = VaultDoorState.SEALED
    trust_level: float = 35.0  # 0 to 100 scale
    puzzle_state: PuzzleState = Field(default_factory=PuzzleState)
    player: PlayerState = Field(default_factory=PlayerState)
    hints_requested: int = 0
    clues_discovered: List[str] = Field(default_factory=list)
    trade_offered: bool = False
    restoration_task_assigned: bool = False
    access_granted: bool = False
    access_denied: bool = False
    session_ended: bool = False
    subsystems_locked: List[str] = Field(default_factory=list)
    relationship_history: List[Dict[str, Any]] = Field(default_factory=list)
    action_log: List[Dict[str, Any]] = Field(default_factory=list)

    def is_terminal_state(self) -> bool:
        return self.session_ended or self.access_granted or self.access_denied
