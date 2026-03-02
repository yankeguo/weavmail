"""
Configuration storage for weavmail accounts.

Accounts are stored in `.weavmail/accounts.json` relative to the current
working directory.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# All required account parameters.
ACCOUNT_PARAMS = [
    "imap_host",
    "imap_port",
    "imap_username",
    "imap_password",
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "addresses",
]


def get_config_path() -> Path:
    """Return the path to the accounts.json config file (relative to cwd)."""
    return Path(".weavmail") / "accounts.json"


def ensure_config_dir() -> None:
    """Create the .weavmail/ directory if it does not exist."""
    config_dir = Path(".weavmail")
    config_dir.mkdir(exist_ok=True)


def load_accounts() -> dict[str, Any]:
    """
    Load accounts from .weavmail/accounts.json.

    Returns an empty dict if the directory or file does not exist.
    Raises SystemExit with an error message if the file contains invalid JSON.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Error: {config_path} contains invalid JSON and may be corrupted.\n"
            f"Details: {exc}"
        )


def save_accounts(accounts: dict[str, Any]) -> None:
    """
    Persist accounts to .weavmail/accounts.json using an atomic write.

    Writes to a temporary file first, then renames it so the config is
    never left in a partially-written state.
    """
    ensure_config_dir()
    config_path = get_config_path()
    config_dir = config_path.parent

    fd, tmp_path = tempfile.mkstemp(dir=config_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, config_path)
    except Exception:
        # Clean up temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
