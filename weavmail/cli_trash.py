import re
import sys
from pathlib import Path

import click
import yaml
from imap_tools import MailBox

from .cli import cli
from .cli_sync import sync_mailbox
from .config import load_accounts

_REQUIRED = ["imap_host", "imap_port", "imap_username", "imap_password"]

_DEFAULT_SYNC_LIMIT = 10


@cli.command()
@click.argument("mail_file", metavar="MAIL_FILE")
@click.option(
    "--account",
    default=None,
    help="Expected account name; if provided, must match the account in the mail's front matter",
)
@click.option(
    "--sync-limit",
    default=_DEFAULT_SYNC_LIMIT,
    show_default=True,
    type=int,
    help="Limit for the follow-up sync on the source mailbox",
)
def trash(mail_file: str, account: str | None, sync_limit: int):
    """Move a mail to the account's trash mailbox, then sync the source mailbox.

    MAIL_FILE is the local .md file path.

    The trash mailbox is read from the account's trash_mailbox configuration.
    An error is raised if trash_mailbox is not configured for the account.

    The account is read from the mail file's front matter. Use --account to
    verify it matches an expected value; an error is raised if they differ.
    """
    src_path = Path(mail_file)
    if not src_path.exists():
        click.echo(f"Error: file not found: {src_path}", err=True)
        sys.exit(1)

    # Parse YAML front matter
    content = src_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        click.echo("Error: file has no YAML front matter.", err=True)
        sys.exit(1)
    parts = content.split("---", 2)
    if len(parts) < 3:
        click.echo("Error: malformed YAML front matter.", err=True)
        sys.exit(1)
    front: dict = yaml.safe_load(parts[1])

    front_account = front.get("account")
    src_mailbox = front.get("mailbox")
    uid = str(front.get("uid", ""))

    if not front_account or not src_mailbox or not uid:
        click.echo("Error: front matter missing account, mailbox or uid.", err=True)
        sys.exit(1)

    if account is not None and account != front_account:
        click.echo(
            f"Error: --account '{account}' does not match the account in front matter '{front_account}'.",
            err=True,
        )
        sys.exit(1)

    account = front_account

    accounts = load_accounts()
    if account not in accounts:
        click.echo(f"Error: Account '{account}' not found.", err=True)
        sys.exit(1)

    data = accounts[account]
    missing = [p for p in _REQUIRED if not data.get(p)]
    if missing:
        click.echo(
            f"Error: Account '{account}' is incomplete, missing: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)

    # Get trash mailbox from account configuration
    dst_mailbox = data.get("trash_mailbox")
    if not dst_mailbox:
        click.echo(
            f"Error: Account '{account}' does not have trash_mailbox configured.",
            err=True,
        )
        sys.exit(1)

    # Execute IMAP move
    with MailBox(data["imap_host"], port=data["imap_port"]).login(
        data["imap_username"], data["imap_password"], initial_folder=src_mailbox
    ) as mb:
        mb.move(uid, dst_mailbox)

    click.echo(
        f"[mail moved to trash]\n"
        f"  file:         {src_path}\n"
        f"  src mailbox:  {src_mailbox}\n"
        f"  trash mailbox:  {dst_mailbox}\n"
    )

    # Sync source mailbox to reflect the move (removes the moved mail locally)
    click.echo(f"[syncing source mailbox: {src_mailbox}]")
    sync_mailbox(account, src_mailbox, sync_limit)
