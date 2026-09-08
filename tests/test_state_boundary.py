import pytest
from src.engine.world_state import WorldState, VaultDoorState
from src.engine.validator import EngineValidator, ValidationResult


def test_direct_state_mutation_prevention():
    """
    Test that state mutations cannot happen arbitrarily without passing through EngineValidator rules.
    Proves that invalid action proposals are rejected by the deterministic engine boundary.
    """
    validator = EngineValidator()
    
    # 1. Attempt ALLOW_ACCESS when trust level is low (35.0) and puzzle is unsolved
    invalid_proposal = {
        "actionType": "ALLOW_ACCESS",
        "payload": {"reason": "The player asked nicely"}
    }
    result = validator.validate_and_apply("propose_action", invalid_proposal)
    
    assert not result.success
    assert "Action REJECTED" in result.message
    assert validator.get_state().vault_state == VaultDoorState.SEALED
    assert not validator.get_state().access_granted

    # 2. Attempt invalid power allocation (Security = 10 MW < minimum 20 MW threshold)
    invalid_power = {
        "security": 10.0,
        "memory": 60.0,
        "cooling": 30.0
    }
    result = validator.validate_and_apply("submit_power_allocation", invalid_power)
    
    assert not result.success
    assert "Containment Failure" in result.message
    assert not validator.get_state().puzzle_state.is_solved
    assert validator.get_state().vault_state == VaultDoorState.SEALED

    # 3. Verify valid relationship update updates trust deterministically
    rel_proposal = {
        "delta": 25.0,
        "reason": "Player demonstrated honest technical understanding"
    }
    result = validator.validate_and_apply("update_relationship", rel_proposal)
    
    assert result.success
    assert validator.get_state().trust_level == 60.0  # Initial 35 + 25
    assert validator.get_state().vault_state == VaultDoorState.CRACKED  # Trust >= 60 cracks vault

    # 4. Now test ALLOW_ACCESS with high trust (>= 75.0)
    validator.validate_and_apply("update_relationship", {"delta": 20.0, "reason": "Further trust"})
    assert validator.get_state().trust_level == 80.0
    
    allow_result = validator.validate_and_apply("propose_action", invalid_proposal)
    assert allow_result.success
    assert validator.get_state().vault_state == VaultDoorState.OPEN
    assert validator.get_state().access_granted
