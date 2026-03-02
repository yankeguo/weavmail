"""
Tests for account management commands and config storage.
"""

import json
import os
import sys

import pytest
from click.testing import CliRunner

from weavmail.cli import cli
from weavmail.config import (
    ACCOUNT_PARAMS,
    ensure_config_dir,
    get_config_path,
    load_accounts,
    save_accounts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_accounts(tmp_path, data):
    """Write accounts.json into tmp_path / .weavmail/."""
    config_dir = tmp_path / ".weavmail"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "accounts.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")


def _read_accounts(tmp_path):
    return json.loads((tmp_path / ".weavmail" / "accounts.json").read_text())


# ---------------------------------------------------------------------------
# 5.1  Creating a new account with all parameters
# ---------------------------------------------------------------------------


def test_create_new_account_all_params(tmp_path, monkeypatch):
    """5.1 - account config with all 9 parameters stores them correctly."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "account",
            "config",
            "myaccount",
            "--imap-host",
            "imap.example.com",
            "--imap-port",
            "993",
            "--imap-username",
            "user@example.com",
            "--imap-password",
            "imapsecret",
            "--smtp-host",
            "smtp.example.com",
            "--smtp-port",
            "587",
            "--smtp-username",
            "user@example.com",
            "--smtp-password",
            "smtpsecret",
            "--addresses",
            "user@example.com, alias@example.com",
        ],
    )
    assert result.exit_code == 0, result.output

    accounts = _read_accounts(tmp_path)
    assert "myaccount" in accounts
    acc = accounts["myaccount"]
    assert acc["imap_host"] == "imap.example.com"
    assert acc["imap_port"] == 993
    assert acc["smtp_port"] == 587
    assert acc["addresses"] == ["user@example.com", "alias@example.com"]


# ---------------------------------------------------------------------------
# 5.2  Updating existing account with partial values
# ---------------------------------------------------------------------------


def test_update_existing_account_partial(tmp_path, monkeypatch):
    """5.2 - Only provided options are updated; omitted options keep existing values."""
    monkeypatch.chdir(tmp_path)
    _write_accounts(
        tmp_path,
        {
            "myaccount": {
                "imap_host": "imap.old.com",
                "imap_username": "old@example.com",
                "imap_password": "oldpw",
                "smtp_host": "smtp.old.com",
                "smtp_username": "old@example.com",
                "smtp_password": "oldsmtppw",
                "imap_port": 143,
                "smtp_port": 25,
                "addresses": ["old@example.com"],
            }
        },
    )
    runner = CliRunner()
    # Change only imap_host; all other fields should be preserved.
    result = runner.invoke(
        cli,
        ["account", "config", "myaccount", "--imap-host", "imap.new.com"],
    )
    assert result.exit_code == 0, result.output

    acc = _read_accounts(tmp_path)["myaccount"]
    assert acc["imap_host"] == "imap.new.com"
    assert acc["imap_username"] == "old@example.com"  # unchanged
    assert acc["smtp_host"] == "smtp.old.com"  # unchanged
    assert acc["imap_port"] == 143  # unchanged


# ---------------------------------------------------------------------------
# 5.3  Account list with complete and incomplete accounts
# ---------------------------------------------------------------------------


def test_account_list_complete_and_incomplete(tmp_path, monkeypatch):
    """5.3 - list shows [complete] and [incomplete] with missing fields."""
    monkeypatch.chdir(tmp_path)
    full_account: dict = {p: "val" for p in ACCOUNT_PARAMS}
    full_account["imap_port"] = 993
    full_account["smtp_port"] = 587
    full_account["addresses"] = ["a@b.com"]

    _write_accounts(
        tmp_path,
        {
            "complete": full_account,
            "partial": {"imap_host": "imap.example.com"},
        },
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["account", "list"])
    assert result.exit_code == 0, result.output
    assert "complete [complete]" in result.output
    assert "partial [incomplete]" in result.output
    assert "Warning:" in result.output


def test_account_list_empty(tmp_path, monkeypatch):
    """5.3 - list shows 'No accounts configured' when empty."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["account", "list"])
    assert result.exit_code == 0, result.output
    assert "No accounts configured" in result.output


# ---------------------------------------------------------------------------
# 5.4  Account delete (existing and non-existing)
# ---------------------------------------------------------------------------


def test_account_delete_existing(tmp_path, monkeypatch):
    """5.4 - delete removes an existing account."""
    monkeypatch.chdir(tmp_path)
    _write_accounts(tmp_path, {"todelete": {"imap_host": "x"}})
    runner = CliRunner()
    result = runner.invoke(cli, ["account", "delete", "todelete"])
    assert result.exit_code == 0, result.output
    assert "todelete" not in _read_accounts(tmp_path)


def test_account_delete_nonexistent(tmp_path, monkeypatch):
    """5.4 - delete of non-existent account exits with code 1."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["account", "delete", "ghost"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


# ---------------------------------------------------------------------------
# 5.5  Default account name
# ---------------------------------------------------------------------------


def test_default_account_name(tmp_path, monkeypatch):
    """5.5 - account config without name argument uses 'default'."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["account", "config", "--imap-host", "imap.example.com"],
    )
    assert result.exit_code == 0, result.output
    accounts = _read_accounts(tmp_path)
    assert "default" in accounts


# ---------------------------------------------------------------------------
# 5.6  Atomic file writes
# ---------------------------------------------------------------------------


def test_atomic_write(tmp_path, monkeypatch):
    """5.6 - save_accounts uses temp-file+rename; no .tmp file left behind."""
    monkeypatch.chdir(tmp_path)
    data = {"acc": {"imap_host": "imap.example.com"}}
    save_accounts(data)

    config_dir = tmp_path / ".weavmail"
    tmp_files = list(config_dir.glob("*.tmp"))
    assert tmp_files == [], f"Temp files left behind: {tmp_files}"

    saved = load_accounts()
    assert saved == data


# ---------------------------------------------------------------------------
# 5.7  Invalid JSON handling
# ---------------------------------------------------------------------------


def test_invalid_json_handling(tmp_path, monkeypatch):
    """5.7 - invalid JSON in accounts.json raises SystemExit with error msg."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".weavmail"
    config_dir.mkdir()
    (config_dir / "accounts.json").write_text("this is not json", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        load_accounts()

    assert (
        "invalid JSON" in str(exc_info.value).lower()
        or "corrupted" in str(exc_info.value).lower()
    )
