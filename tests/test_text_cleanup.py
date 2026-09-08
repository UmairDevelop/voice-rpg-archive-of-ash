import pytest
from src.voice.cleanup import clean_text_for_speech


def test_clean_text_for_speech_stage_directions():
    raw = "*sighs* Power allocation is severely limited. [pauses] Please proceed cautiously."
    cleaned = clean_text_for_speech(raw)
    assert "*sighs*" not in cleaned
    assert "[pauses]" not in cleaned
    assert "Power allocation is severely limited. Please proceed cautiously." in cleaned


def test_clean_text_for_speech_markdown():
    raw = "## Warning!\n**Security** levels are `CRITICAL`. Refer to [documentation](http://lore.local)."
    cleaned = clean_text_for_speech(raw)
    assert "##" not in cleaned
    assert "**" not in cleaned
    assert "`CRITICAL`" not in cleaned
    assert "Warning! Security levels are CRITICAL. Refer to documentation." in cleaned


def test_clean_text_for_speech_json_leakage():
    raw = "Adjusting grid... {\"actionType\": \"UPDATE_RELATIONSHIP\", \"delta\": 10} Done."
    cleaned = clean_text_for_speech(raw)
    assert "actionType" not in cleaned
    assert "Adjusting grid ... Done." in cleaned


def test_clean_text_for_speech_pacing():
    raw = "System standby---retrieving schematics"
    cleaned = clean_text_for_speech(raw)
    assert "---" not in cleaned
    assert "System standby -- retrieving schematics." in cleaned
