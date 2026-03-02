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
@click.argument("name", default="default", metavar="NAME")
@click.option(
    "--imap-host", default=None, help="IMAP server hostname, e.g. imap.gmail.com"
)
@click.option(
    "--imap-port",
    default=None,
    type=int,
    help=f"IMAP server port, defaults to {IMAP_DEFAULT_PORT} (IMAPS/TLS) on first creation",
)
@click.option(
    "--imap-username",
    default=None,
    help="IMAP login username, usually the full email address",
)
@click.option(
    "--imap-password", default=None, help="IMAP login password or app-specific password"
)
@click.option(
    "--smtp-host", default=None, help="SMTP server hostname, e.g. smtp.gmail.com"
)
@click.option(
    "--smtp-port",
    default=None,
    type=int,
    help=f"SMTP server port, defaults to {SMTP_DEFAULT_PORT} (SMTPS/TLS) on first creation",
)
@click.option(
    "--smtp-username",
    default=None,
    help="SMTP login username, usually the full email address",
)
@click.option(
    "--smtp-password", default=None, help="SMTP login password or app-specific password"
)
@click.option(
    "--username",
    default=None,
    help="Set both imap-username and smtp-username in one option",
)
@click.option(
    "--password",
    default=None,
    help="Set both imap-password and smtp-password in one option",
)
@click.option(
    "--addresses",
    default=None,
    help="Comma-separated list of email addresses associated with this account, used as valid sender addresses",
)
@click.option(
    "--sent-mailbox",
    default=None,
    help="Mailbox name to save sent mail to, e.g. 'Sent' or '[Gmail]/Sent Mail'",
)
@click.option(
    "--trash-mailbox",
    default=None,
    help="Mailbox name for trash, e.g. 'Trash' or '[Gmail]/Trash'",
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
    username,
    password,
    addresses,
    sent_mailbox,
    trash_mailbox,
):
    """Create or update an account configuration.

    NAME is the account identifier (default: "default"). Only the options
    provided will be updated; omitted options keep their existing values.
    Port fields default to TLS standard values (IMAP: 993, SMTP: 465) only
    when first creating the account.

    Use --username / --password as shorthand to set both IMAP and SMTP
    credentials at once. Explicit --imap-* / --smtp-* options take precedence.
    """
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
    elif username is not None:
        data["imap_username"] = username
    if imap_password is not None:
        data["imap_password"] = imap_password
    elif password is not None:
        data["imap_password"] = password
    if smtp_host is not None:
        data["smtp_host"] = smtp_host
    if smtp_port is not None:
        data["smtp_port"] = smtp_port
    elif "smtp_port" not in data:
        data["smtp_port"] = SMTP_DEFAULT_PORT
    if smtp_username is not None:
        data["smtp_username"] = smtp_username
    elif username is not None:
        data["smtp_username"] = username
    if smtp_password is not None:
        data["smtp_password"] = smtp_password
    elif password is not None:
        data["smtp_password"] = password
    if addresses is not None:
        data["addresses"] = [a.strip() for a in addresses.split(",") if a.strip()]
    if sent_mailbox is not None:
        data["sent_mailbox"] = sent_mailbox
    if trash_mailbox is not None:
        data["trash_mailbox"] = trash_mailbox

    accounts[name] = data
    save_accounts(accounts)
    click.echo(f"Account '{name}' saved.")

    # Print all configured parameters; mask password values
    _MASKED = {"imap_password", "smtp_password"}
    for key, value in data.items():
        if value is None:
            continue
        if key in _MASKED:
            click.echo(f"  {key}: ********")
        else:
            click.echo(f"  {key}: {value}")

    missing = _missing_params(data)
    if missing:
        click.echo(f"Warning: incomplete configuration, missing: {', '.join(missing)}")


@account.command("delete")
@click.argument("name", metavar="NAME")
def account_delete(name: str):
    """Delete an account configuration.

    NAME is the account identifier to remove.
    """
    accounts = load_accounts()
    if name not in accounts:
        click.echo(f"Error: Account '{name}' not found.", err=True)
        sys.exit(1)
    del accounts[name]
    save_accounts(accounts)
    click.echo(f"Account '{name}' deleted.")
