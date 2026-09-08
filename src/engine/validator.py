from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

from .world_state import WorldState, VaultDoorState
from .actions import (
    SkillType,
    ActionType,
    EvaluateSkillCheck,
    SubmitPowerAllocation,
    ProposeAction,
    UpdateRelationship,
    RequestHint,
)
from .puzzle_solver import validate_power_allocation


class ValidationResult(BaseModel):
    success: bool
    message: str
    action_type: str
    state_diff: Dict[str, Any] = Field(default_factory=dict)


class EngineValidator:
    """
    Deterministic Engine Boundary.
    Enforces that LLM / UI tool proposals cannot directly mutate WorldState without passing validation.
    """
    def __init__(self, initial_state: Optional[WorldState] = None):
        self.state = initial_state or WorldState()

    def get_state(self) -> WorldState:
        return self.state

    def validate_and_apply(self, tool_name: str, arguments: Dict[str, Any]) -> ValidationResult:
        """
        Validates raw tool call arguments against Pydantic schema and current WorldState.
        Applies mutation ONLY if valid. Returns ValidationResult.
        """
        # Log action attempt
        log_entry = {"tool_name": tool_name, "arguments": arguments}

        if tool_name == "evaluate_skill_check":
            return self._handle_evaluate_skill_check(arguments, log_entry)
        elif tool_name == "submit_power_allocation":
            return self._handle_submit_power_allocation(arguments, log_entry)
        elif tool_name == "update_relationship":
            return self._handle_update_relationship(arguments, log_entry)
        elif tool_name == "request_hint":
            return self._handle_request_hint(arguments, log_entry)
        elif tool_name == "propose_action":
            return self._handle_propose_action(arguments, log_entry)
        else:
            res = ValidationResult(
                success=False,
                message=f"Unknown tool call '{tool_name}' rejected.",
                action_type="UNKNOWN",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

    def _handle_evaluate_skill_check(self, args: Dict[str, Any], log_entry: dict) -> ValidationResult:
        try:
            model = EvaluateSkillCheck(**args)
        except ValidationError as e:
            res = ValidationResult(
                success=False,
                message=f"Invalid EvaluateSkillCheck schema: {str(e)}",
                action_type="evaluate_skill_check",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        # Trust modifies effective DC
        trust_bonus = (self.state.trust_level - 50.0) / 10.0
        effective_dc = max(5.0, model.targetDC - trust_bonus)
        
        # Skill check evaluation: baseline engine rule
        # DC calculation outcome based on trust & skill type
        passed = self.state.trust_level >= (effective_dc * 2.0)
        
        if passed:
            self.state.trust_level = min(100.0, self.state.trust_level + 10.0)
            msg = f"Skill check {model.skillType.value} passed against DC {effective_dc:.1f} (Target DC: {model.targetDC}). Trust increased to {self.state.trust_level:.1f}."
            diff = {"trust_level": self.state.trust_level, "passed": True}
            res = ValidationResult(success=True, message=msg, action_type="evaluate_skill_check", state_diff=diff)
        else:
            msg = f"Skill check {model.skillType.value} failed against DC {effective_dc:.1f} (Target DC: {model.targetDC})."
            diff = {"passed": False}
            res = ValidationResult(success=False, message=msg, action_type="evaluate_skill_check", state_diff=diff)

        log_entry["result"] = res.model_dump()
        self.state.action_log.append(log_entry)
        return res

    def _handle_submit_power_allocation(self, args: Dict[str, Any], log_entry: dict) -> ValidationResult:
        try:
            model = SubmitPowerAllocation(**args)
        except ValidationError as e:
            res = ValidationResult(
                success=False,
                message=f"Invalid SubmitPowerAllocation schema: {str(e)}",
                action_type="submit_power_allocation",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        self.state.puzzle_state.attempts += 1
        self.state.puzzle_state.security = model.security
        self.state.puzzle_state.memory = model.memory
        self.state.puzzle_state.cooling = model.cooling

        is_valid, msg = validate_power_allocation(model.security, model.memory, model.cooling)

        if is_valid:
            self.state.puzzle_state.is_solved = True
            self.state.puzzle_state.last_error = None
            self.state.vault_state = VaultDoorState.OPEN
            self.state.access_granted = True
            diff = {
                "puzzle_solved": True,
                "vault_state": VaultDoorState.OPEN.value,
                "access_granted": True,
            }
            res = ValidationResult(success=True, message=msg, action_type="submit_power_allocation", state_diff=diff)
        else:
            self.state.puzzle_state.is_solved = False
            self.state.puzzle_state.last_error = msg
            diff = {"puzzle_solved": False, "last_error": msg}
            res = ValidationResult(success=False, message=msg, action_type="submit_power_allocation", state_diff=diff)

        log_entry["result"] = res.model_dump()
        self.state.action_log.append(log_entry)
        return res

    def _handle_update_relationship(self, args: Dict[str, Any], log_entry: dict) -> ValidationResult:
        try:
            model = UpdateRelationship(**args)
        except ValidationError as e:
            res = ValidationResult(
                success=False,
                message=f"Invalid UpdateRelationship schema: {str(e)}",
                action_type="update_relationship",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        old_trust = self.state.trust_level
        new_trust = max(0.0, min(100.0, old_trust + model.delta))
        self.state.trust_level = new_trust
        
        self.state.relationship_history.append({
            "old": old_trust,
            "new": new_trust,
            "delta": model.delta,
            "reason": model.reason,
        })

        if new_trust >= 60.0 and self.state.vault_state == VaultDoorState.SEALED:
            self.state.vault_state = VaultDoorState.CRACKED

        diff = {"trust_level": new_trust, "delta": model.delta, "reason": model.reason}
        res = ValidationResult(
            success=True,
            message=f"Relationship updated by {model.delta:+.1f} (New Trust: {new_trust:.1f}). Reason: {model.reason}",
            action_type="update_relationship",
            state_diff=diff,
        )

        log_entry["result"] = res.model_dump()
        self.state.action_log.append(log_entry)
        return res

    def _handle_request_hint(self, args: Dict[str, Any], log_entry: dict) -> ValidationResult:
        try:
            model = RequestHint(**args)
        except ValidationError as e:
            res = ValidationResult(
                success=False,
                message=f"Invalid RequestHint schema: {str(e)}",
                action_type="request_hint",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        if model.level < 1 or model.level > 3:
            res = ValidationResult(
                success=False,
                message="Hint level must be between 1 and 3.",
                action_type="request_hint",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        self.state.hints_requested += 1

        hint_messages = {
            1: "Archivist Note: Grid capacity is locked at exactly 100 MW total. Security requires a containment baseline of at least 20 MW.",
            2: "Archivist Note: Schematic decompression requires at least 40 MW memory load, which generates proportional heat requiring cooling = (memory / 2) + 10 MW.",
            3: "Archivist Note: Excess security above 40 MW triggers lockdown. For 40 MW memory, set Cooling to 30 MW and Security to 30 MW.",
        }

        hint_text = hint_messages.get(model.level, hint_messages[1])
        diff = {"hints_requested": self.state.hints_requested, "level": model.level, "hint": hint_text}

        res = ValidationResult(
            success=True,
            message=hint_text,
            action_type="request_hint",
            state_diff=diff,
        )

        log_entry["result"] = res.model_dump()
        self.state.action_log.append(log_entry)
        return res

    def _handle_propose_action(self, args: Dict[str, Any], log_entry: dict) -> ValidationResult:
        try:
            model = ProposeAction(**args)
        except ValidationError as e:
            res = ValidationResult(
                success=False,
                message=f"Invalid ProposeAction schema: {str(e)}",
                action_type="propose_action",
            )
            log_entry["result"] = res.model_dump()
            self.state.action_log.append(log_entry)
            return res

        action_type = model.actionType
        payload = model.payload

        if action_type == ActionType.ALLOW_ACCESS:
            # Deterministic check: requires trust >= 75 OR solved puzzle
            if self.state.trust_level >= 75.0 or self.state.puzzle_state.is_solved:
                self.state.vault_state = VaultDoorState.OPEN
                self.state.access_granted = True
                diff = {"vault_state": VaultDoorState.OPEN.value, "access_granted": True}
                res = ValidationResult(
                    success=True,
                    message="Action APPROVED: Vault door unlocked and access granted to water schematics.",
                    action_type="propose_action:ALLOW_ACCESS",
                    state_diff=diff,
                )
            else:
                res = ValidationResult(
                    success=False,
                    message=f"Action REJECTED: Insufficient authorization. Trust level is {self.state.trust_level:.1f} (requires 75.0+) and power grid is unsolved.",
                    action_type="propose_action:ALLOW_ACCESS",
                )

        elif action_type == ActionType.DENY_ACCESS:
            self.state.access_denied = True
            self.state.session_ended = True
            diff = {"access_denied": True, "session_ended": True}
            res = ValidationResult(
                success=True,
                message="Action APPROVED: Access permanently denied to the archive.",
                action_type="propose_action:DENY_ACCESS",
                state_diff=diff,
            )

        elif action_type == ActionType.REVEAL_CLUE:
            clue = payload.get("clue", "Archive diagnostic log reveals thermal cooling parameters.")
            if clue not in self.state.clues_discovered:
                self.state.clues_discovered.append(clue)
            if self.state.trust_level >= 50.0 and self.state.vault_state == VaultDoorState.SEALED:
                self.state.vault_state = VaultDoorState.CRACKED
            diff = {"clues_discovered": self.state.clues_discovered, "vault_state": self.state.vault_state.value}
            res = ValidationResult(
                success=True,
                message=f"Action APPROVED: Environmental clue revealed: {clue}",
                action_type="propose_action:REVEAL_CLUE",
                state_diff=diff,
            )

        elif action_type == ActionType.OFFER_TRADEOFF:
            self.state.trade_offered = True
            diff = {"trade_offered": True}
            res = ValidationResult(
                success=True,
                message="Action APPROVED: Power trade-off condition offered to player.",
                action_type="propose_action:OFFER_TRADEOFF",
                state_diff=diff,
            )

        elif action_type == ActionType.ASSIGN_RESTORATION_TASK:
            self.state.restoration_task_assigned = True
            diff = {"restoration_task_assigned": True}
            res = ValidationResult(
                success=True,
                message="Action APPROVED: System restoration task assigned.",
                action_type="propose_action:ASSIGN_RESTORATION_TASK",
                state_diff=diff,
            )

        elif action_type == ActionType.LOCK_SUBSYSTEM:
            subsystem = payload.get("subsystem", "Security")
            if subsystem not in self.state.subsystems_locked:
                self.state.subsystems_locked.append(subsystem)
            self.state.trust_level = max(0.0, self.state.trust_level - 10.0)
            diff = {"subsystems_locked": self.state.subsystems_locked, "trust_level": self.state.trust_level}
            res = ValidationResult(
                success=True,
                message=f"Action APPROVED: Subsystem '{subsystem}' locked down due to security concern.",
                action_type="propose_action:LOCK_SUBSYSTEM",
                state_diff=diff,
            )

        elif action_type == ActionType.END_CONVERSATION:
            self.state.session_ended = True
            diff = {"session_ended": True}
            res = ValidationResult(
                success=True,
                message="Action APPROVED: Session concluded.",
                action_type="propose_action:END_CONVERSATION",
                state_diff=diff,
            )

        else:
            diff = {"payload": payload}
            res = ValidationResult(
                success=True,
                message=f"Action APPROVED: Proposed action '{action_type.value}' logged.",
                action_type=f"propose_action:{action_type.value}",
                state_diff=diff,
            )

        log_entry["result"] = res.model_dump()
        self.state.action_log.append(log_entry)
        return res
