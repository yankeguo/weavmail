"""
Configuration storage for weavmail accounts.

Accounts are stored in `.weavmail/accounts.json` relative to the current
working directory.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import click
import yaml

# All required account parameters (used for completeness checks).
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

# Required fields for IMAP operations.
IMAP_REQUIRED = ["imap_host", "imap_port", "imap_username", "imap_password"]

# Required fields for SMTP operations.
SMTP_REQUIRED = ["smtp_host", "smtp_port", "smtp_username", "smtp_password"]


def get_config_path() -> Path:
    """Return the path to the accounts.json config file (relative to cwd)."""
    return Path(".weavmail") / "accounts.json"


def ensure_config_dir() -> None:
    """Create the .weavmail/ directory if it does not exist."""
    Path(".weavmail").mkdir(exist_ok=True)


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
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def missing_params(data: dict, params: list[str] = ACCOUNT_PARAMS) -> list[str]:
    """Return the subset of *params* that are absent or falsy in *data*."""
    return [p for p in params if not data.get(p)]


def require_account_fields(account: str, data: dict, fields: list[str]) -> None:
    """
    Exit with an error message if any of *fields* are missing from *data*.

    Called at command execution time (not at config time) to enforce that the
    necessary parameters have been set before an operation is attempted.
    """
    missing = missing_params(data, fields)
    if missing:
        click.echo(
            f"Error: Account '{account}' is missing required fields: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)


def load_account(account: str) -> dict[str, Any]:
    """
    Load a single named account from config, exiting with an error if not found.
    """
    accounts = load_accounts()
    if account not in accounts:
        click.echo(f"Error: Account '{account}' not found.", err=True)
        sys.exit(1)
    return accounts[account]


def safe_dirname(name: str) -> str:
    """Replace characters that are unsafe in directory/file names with underscores."""
    return re.sub(r"[^\w\-.]", "_", name)


def parse_front_matter(path: Path) -> tuple[dict, str]:
    """
    Parse YAML front matter and body from a .md file.

    Returns a (front_matter_dict, body_str) tuple.
    Calls sys.exit(1) with a descriptive error if the file is malformed.
    """
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        click.echo(f"Error: {path}: file has no YAML front matter.", err=True)
        sys.exit(1)
    parts = content.split("---", 2)
    if len(parts) < 3:
        click.echo(f"Error: {path}: malformed YAML front matter.", err=True)
        sys.exit(1)
    return yaml.safe_load(parts[1]), parts[2].strip()
