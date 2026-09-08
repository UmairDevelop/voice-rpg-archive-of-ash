import pytest
from src.engine.puzzle_solver import validate_power_allocation


def test_puzzle_solver_constraints():
    # Valid solution
    valid, msg = validate_power_allocation(security=30.0, memory=40.0, cooling=30.0)
    assert valid
    assert "Power grid stabilized" in msg

    # Imbalanced sum
    valid, msg = validate_power_allocation(security=30.0, memory=40.0, cooling=20.0)
    assert not valid
    assert "Power sum imbalance" in msg

    # Security below 20
    valid, msg = validate_power_allocation(security=15.0, memory=50.0, cooling=35.0)
    assert not valid
    assert "Containment Failure" in msg

    # Security above 40
    valid, msg = validate_power_allocation(security=45.0, memory=40.0, cooling=15.0)
    assert not valid
    assert "Security Override Active" in msg

    # Memory below 40
    valid, msg = validate_power_allocation(security=35.0, memory=35.0, cooling=30.0)
    assert not valid
    assert "Insufficient Buffer" in msg

    # Cooling under heat load
    valid, msg = validate_power_allocation(security=25.0, memory=50.0, cooling=25.0)  # Cooling needed: 50/2 + 10 = 35
    assert not valid
    assert "Thermal Overheat Warning" in msg
