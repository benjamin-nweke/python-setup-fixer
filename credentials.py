"""Read only the app's backend credential, never a selected project's env file."""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent


def backend_key():
    key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if key:
        return key
    try:
        content = (APP_ROOT / '.env').read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return ''
    for line in content.splitlines():
        name, separator, value = line.strip().partition('=')
        if separator and name.strip() == 'ANTHROPIC_API_KEY':
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            return value.strip()
    return ''
