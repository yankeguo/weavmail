import click

from .cli import cli
from .config import load_accounts, missing_params, save_accounts

# Default ports for IMAP/SMTP over TLS
IMAP_DEFAULT_PORT = 993
SMTP_DEFAULT_PORT = 465


@cli.group("account")
def account():
    """Manage mail accounts"""
    pass


@account.command("list")
def account_list():
    """List all configured accounts"""
    accounts = load_accounts()
    if not accounts:
        click.echo("No accounts configured")
        return

    for name, data in accounts.items():
        absent = missing_params(data)
        if absent:
            click.echo(f"{name} [incomplete]")
            click.echo(f"  Warning: missing parameters: {', '.join(absent)}")
        else:
            click.echo(f"{name} [complete]")


@account.command("config")
@click.argument("name", default="default", metavar="NAME")
@click.option("--imap-host", default=None, help="IMAP server hostname")
@click.option(
    "--imap-port",
    default=None,
    type=int,
    help=f"IMAP server port (default {IMAP_DEFAULT_PORT} on first creation)",
)
@click.option("--imap-username", default=None, help="IMAP login username")
@click.option(
    "--imap-password", default=None, help="IMAP login password or app password"
)
@click.option("--smtp-host", default=None, help="SMTP server hostname")
@click.option(
    "--smtp-port",
    default=None,
    type=int,
    help=f"SMTP server port (default {SMTP_DEFAULT_PORT} on first creation)",
)
@click.option("--smtp-username", default=None, help="SMTP login username")
@click.option(
    "--smtp-password", default=None, help="SMTP login password or app password"
)
@click.option(
    "--username",
    default=None,
    help="Shorthand: set both --imap-username and --smtp-username",
)
@click.option(
    "--password",
    default=None,
    help="Shorthand: set both --imap-password and --smtp-password",
)
@click.option(
    "--addresses",
    default=None,
    help="Comma-separated list of sender addresses for this account",
)
@click.option(
    "--sent-mailbox",
    default=None,
    help="Mailbox to save sent mail to, e.g. 'Sent' or '[Gmail]/Sent Mail'",
)
@click.option(
    "--trash-mailbox",
    default=None,
    help="Trash mailbox name, e.g. 'Trash' or '[Gmail]/Trash'",
)
@click.option(
    "--archive-mailbox",
    default=None,
    help="Archive mailbox name, e.g. 'Archive' or '[Gmail]/All Mail'",
)
def account_config(
    name,
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
    archive_mailbox,
):
    """Create or update an account configuration.

    NAME is the account identifier (default: "default"). Only the options
    provided will be updated; omitted options keep their existing values.
    Default ports (IMAP: 993, SMTP: 465) are set only on first creation.

    --username / --password are shorthand for setting both IMAP and SMTP
    credentials at once; explicit --imap-* / --smtp-* options take precedence.
    """
    accounts = load_accounts()
    data: dict = accounts.get(name, {})
    is_new = name not in accounts

    # IMAP settings
    if imap_host is not None:
        data["imap_host"] = imap_host
    if imap_port is not None:
        data["imap_port"] = imap_port
    elif is_new:
        data["imap_port"] = IMAP_DEFAULT_PORT
    if imap_username is not None:
        data["imap_username"] = imap_username
    elif username is not None:
        data["imap_username"] = username
    if imap_password is not None:
        data["imap_password"] = imap_password
    elif password is not None:
        data["imap_password"] = password

    # SMTP settings
    if smtp_host is not None:
        data["smtp_host"] = smtp_host
    if smtp_port is not None:
        data["smtp_port"] = smtp_port
    elif is_new:
        data["smtp_port"] = SMTP_DEFAULT_PORT
    if smtp_username is not None:
        data["smtp_username"] = smtp_username
    elif username is not None:
        data["smtp_username"] = username
    if smtp_password is not None:
        data["smtp_password"] = smtp_password
    elif password is not None:
        data["smtp_password"] = password

    # Optional fields
    if addresses is not None:
        data["addresses"] = [a.strip() for a in addresses.split(",") if a.strip()]
    if sent_mailbox is not None:
        data["sent_mailbox"] = sent_mailbox
    if trash_mailbox is not None:
        data["trash_mailbox"] = trash_mailbox
    if archive_mailbox is not None:
        data["archive_mailbox"] = archive_mailbox

    accounts[name] = data
    save_accounts(accounts)
    click.echo(f"Account '{name}' saved.")

    # Print current configuration (mask passwords)
    _MASKED = {"imap_password", "smtp_password"}
    for key, value in data.items():
        if value is None:
            continue
        display = "********" if key in _MASKED else value
        click.echo(f"  {key}: {display}")

    absent = missing_params(data)
    if absent:
        click.echo(f"Warning: incomplete configuration, missing: {', '.join(absent)}")

    missing_mailboxes = [
        f"--{f.replace('_', '-')}"
        for f in ("sent_mailbox", "trash_mailbox", "archive_mailbox")
        if not data.get(f)
    ]
    if missing_mailboxes:
        click.echo(
            f"Hint: {', '.join(missing_mailboxes)} not configured. "
            f"Run `weavmail mailbox` to list available folders, "
            f"then set the appropriate options with `weavmail account config {name}`."
        )


@account.command("delete")
@click.argument("name", metavar="NAME")
def account_delete(name: str):
    """Delete an account configuration."""
    accounts = load_accounts()
    if name not in accounts:
        click.echo(f"Error: Account '{name}' not found.", err=True)
        raise SystemExit(1)
    del accounts[name]
    save_accounts(accounts)
    click.echo(f"Account '{name}' deleted.")
