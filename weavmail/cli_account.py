import sys

import click

from .cli import cli
from .config import ACCOUNT_PARAMS, load_accounts, save_accounts

# Default ports for IMAP/SMTP over TLS
IMAP_DEFAULT_PORT = 993
SMTP_DEFAULT_PORT = 465


@cli.group("account")
def account():
    """Manage mail accounts"""
    pass


def _missing_params(data: dict) -> list[str]:
    return [p for p in ACCOUNT_PARAMS if not data.get(p)]


@account.command("list")
def account_list():
    """List all configured accounts"""
    accounts = load_accounts()
    if not accounts:
        click.echo("No accounts configured")
        return

    for name, data in accounts.items():
        missing = _missing_params(data)
        if missing:
            click.echo(f"{name} [incomplete]")
            click.echo(f"  Warning: missing parameters: {', '.join(missing)}")
        else:
            click.echo(f"{name} [complete]")


@account.command("config")
@click.argument("name", default="default")
@click.option("--imap-host", default=None, help="IMAP server hostname")
@click.option(
    "--imap-port",
    default=None,
    type=int,
    help=f"IMAP server port (default: {IMAP_DEFAULT_PORT})",
)
@click.option("--imap-username", default=None, help="IMAP username")
@click.option("--imap-password", default=None, help="IMAP password")
@click.option("--smtp-host", default=None, help="SMTP server hostname")
@click.option(
    "--smtp-port",
    default=None,
    type=int,
    help=f"SMTP server port (default: {SMTP_DEFAULT_PORT})",
)
@click.option("--smtp-username", default=None, help="SMTP username")
@click.option("--smtp-password", default=None, help="SMTP password")
@click.option(
    "--addresses", default=None, help="Comma-separated list of email addresses"
)
def account_config(
    name: str,
    imap_host,
    imap_port,
    imap_username,
    imap_password,
    smtp_host,
    smtp_port,
    smtp_username,
    smtp_password,
    addresses,
):
    """Create or update an account configuration"""
    accounts = load_accounts()
    data: dict = accounts.get(name, {})

    if imap_host is not None:
        data["imap_host"] = imap_host
    if imap_port is not None:
        data["imap_port"] = imap_port
    elif "imap_port" not in data:
        data["imap_port"] = IMAP_DEFAULT_PORT
    if imap_username is not None:
        data["imap_username"] = imap_username
    if imap_password is not None:
        data["imap_password"] = imap_password
    if smtp_host is not None:
        data["smtp_host"] = smtp_host
    if smtp_port is not None:
        data["smtp_port"] = smtp_port
    elif "smtp_port" not in data:
        data["smtp_port"] = SMTP_DEFAULT_PORT
    if smtp_username is not None:
        data["smtp_username"] = smtp_username
    if smtp_password is not None:
        data["smtp_password"] = smtp_password
    if addresses is not None:
        data["addresses"] = [a.strip() for a in addresses.split(",") if a.strip()]

    accounts[name] = data
    save_accounts(accounts)
    click.echo(f"Account '{name}' saved.")

    missing = _missing_params(data)
    if missing:
        click.echo(f"Warning: incomplete configuration, missing: {', '.join(missing)}")


@account.command("delete")
@click.argument("name")
def account_delete(name: str):
    """Delete an account"""
    accounts = load_accounts()
    if name not in accounts:
        click.echo(f"Error: Account '{name}' not found.", err=True)
        sys.exit(1)
    del accounts[name]
    save_accounts(accounts)
    click.echo(f"Account '{name}' deleted.")
