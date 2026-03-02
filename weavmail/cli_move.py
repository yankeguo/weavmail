from pathlib import Path

import click
from imap_tools import MailBox

from .cli import cli
from .cli_sync import sync_mailbox
from .config import (
    IMAP_REQUIRED,
    load_account,
    parse_front_matter,
    require_account_fields,
)

_DEFAULT_SYNC_LIMIT = 10


@cli.command()
@click.argument("mail_file", metavar="MAIL_FILE")
@click.argument("dst_mailbox", metavar="DST_MAILBOX")
@click.option(
    "--account",
    default=None,
    help="Expected account name; must match the account in the mail's front matter if provided",
)
@click.option(
    "--sync-limit",
    default=_DEFAULT_SYNC_LIMIT,
    show_default=True,
    type=int,
    help="Limit for the follow-up sync on the source mailbox",
)
def move(mail_file: str, dst_mailbox: str, account: str | None, sync_limit: int):
    """Move a mail to another mailbox, then sync the source mailbox.

    MAIL_FILE is the local .md file path.
    DST_MAILBOX is the destination mailbox name on the server.

    The account is read from the mail file's front matter. Use --account to
    verify it matches an expected value.
    """
    src_path = Path(mail_file)
    if not src_path.exists():
        click.echo(f"Error: file not found: {src_path}", err=True)
        raise SystemExit(1)

    front, _ = parse_front_matter(src_path)

    front_account = front.get("account")
    src_mailbox = front.get("mailbox")
    uid = str(front.get("uid", ""))

    if not front_account or not src_mailbox or not uid:
        click.echo(
            f"Error: {src_path}: front matter missing account, mailbox, or uid.",
            err=True,
        )
        raise SystemExit(1)

    if account is not None and account != front_account:
        click.echo(
            f"Error: --account '{account}' does not match front matter account '{front_account}'.",
            err=True,
        )
        raise SystemExit(1)

    account = front_account
    assert account is not None
    data = load_account(account)
    require_account_fields(account, data, IMAP_REQUIRED)

    with MailBox(data["imap_host"], port=data["imap_port"]).login(
        data["imap_username"], data["imap_password"], initial_folder=src_mailbox
    ) as mb:
        mb.move(uid, dst_mailbox)

    click.echo(
        f"[mail moved]\n"
        f"  file:        {src_path}\n"
        f"  src mailbox: {src_mailbox}\n"
        f"  dst mailbox: {dst_mailbox}\n"
    )

    click.echo(f"[syncing source mailbox: {src_mailbox}]")
    sync_mailbox(account, src_mailbox, sync_limit)
