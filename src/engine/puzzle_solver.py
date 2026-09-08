from typing import Tuple, Optional


def validate_power_allocation(
    security: float,
    memory: float,
    cooling: float,
    total_power: float = 100.0
) -> Tuple[bool, str]:
    """
    Deterministic solver for the Archivist Power Allocation puzzle.
    
    Fixed Constraints:
    1. security + memory + cooling == total_power (100 MW)
    2. security >= 20.0 MW (Minimum containment baseline)
    3. security <= 40.0 MW (Excess security locks vault door override controls)
    4. memory >= 40.0 MW (Minimum memory required to decompress water schematics)
    5. cooling >= (memory / 2.0) + 10.0 MW (Thermal stability constraint)
    
    Returns:
        (is_valid, message)
    """
    # 1. Total power budget check
    current_total = security + memory + cooling
    if abs(current_total - total_power) > 0.1:
        return False, f"Power sum imbalance: total allocation is {current_total:.1f} MW, but grid total must equal {total_power:.1f} MW."

    # 2. Security lower bound
    if security < 20.0:
        return False, "Containment Failure: Security allocation below 20.0 MW risks physical containment breach."

    # 3. Security upper bound
    if security > 40.0:
        return False, "Security Override Active: Security allocation above 40.0 MW locks vault override relays."

    # 4. Memory requirement
    if memory < 40.0:
        return False, "Insufficient Buffer: Memory allocation below 40.0 MW cannot decompress schematic archives."

    # 5. Thermal cooling requirement
    required_cooling = (memory / 2.0) + 10.0
    if cooling < required_cooling:
        return False, f"Thermal Overheat Warning: Cooling allocation ({cooling:.1f} MW) is below required thermal threshold ({required_cooling:.1f} MW for {memory:.1f} MW memory load)."

    return True, "Power grid stabilized. Archive schematics un-corrupted and vault unlocked."
