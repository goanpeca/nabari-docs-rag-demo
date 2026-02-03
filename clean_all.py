#!/usr/bin/env python3
"""Remove emojis from all Python files."""

import re
from pathlib import Path


def remove_emojis(text):
    """Remove emoji characters from text."""
    # Emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


# Files to clean
files = [
    "agent.py",
    "ingest_docs.py",
    "app.py",
    "debug_db.py",
    "check_account.py",
    "test_api.py",
]

for filepath in files:
    path = Path(filepath)
    if not path.exists():
        print(f"Skipping {filepath} (not found)")
        continue

    content = path.read_text()
    cleaned = remove_emojis(content)

    if content != cleaned:
        path.write_text(cleaned)
        print(f"Cleaned {filepath}")
    else:
        print(f"No emojis in {filepath}")

print("Done!")
