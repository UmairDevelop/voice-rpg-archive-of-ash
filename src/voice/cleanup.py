import re


def clean_text_for_speech(text: str) -> str:
    """
    Pure-function text cleanup pipeline for streaming TTS voice synthesis.
    """
    if not text:
        return ""

    cleaned = text

    # 1. Strip Markdown links FIRST
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # 2. Strip raw JSON / dict syntax or tool call leakage
    cleaned = re.sub(r'\{[^{}]*\}', '', cleaned)
    cleaned = re.sub(r'\b[A-Za-z0-9_]+\((?:[^{}]*)\)', '', cleaned)

    # 3. Convert bold markdown **text** -> text FIRST
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)

    # 4. Strip single asterisk stage directions (*sighs*, *pauses*) & bracketed directions ([pauses], (clicks))
    cleaned = re.sub(r'(?<!\*)\*([a-zA-Z\s]+)\*(?!\*)', '', cleaned)
    cleaned = re.sub(r'\[+[a-zA-Z\s]+\]+', '', cleaned)
    cleaned = re.sub(r'\(+[a-zA-Z\s]+\)+', '', cleaned)

    # 5. Strip Markdown headers & inline code tags
    cleaned = re.sub(r'^#+\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)

    # 6. Inject pacing punctuation & normalize ellipsis
    cleaned = re.sub(r'\.\.\.+', ' ... ', cleaned)
    cleaned = re.sub(r'--+', ' -- ', cleaned)

    # 7. Clean extra spaces & trailing noise
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if cleaned and cleaned[-1] not in ['.', '!', '?', ':', ';']:
        cleaned += '.'

    return cleaned
