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
@click.argument(
    "mail_files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True),
    metavar="MAIL_FILE [MAIL_FILE ...]",
)
@click.option(
    "--sync-limit",
    default=_DEFAULT_SYNC_LIMIT,
    show_default=True,
    type=int,
    help="Limit for the follow-up sync on the source mailbox",
)
def archive(mail_files: tuple[str, ...], sync_limit: int):
    """Move mails to the account's configured archive mailbox, then sync.

    MAIL_FILE is the local .md file path. Multiple files can be passed for batch
    operations.

    The archive mailbox is read from each mail's account archive_mailbox setting.
    An error is raised if archive_mailbox is not configured for any account.

    Account is read from each mail file's front matter.
    """
    records: list[tuple[Path, str, str, str, str]] = []

    for f in mail_files:
        src_path = Path(f)
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

        data = load_account(front_account)
        require_account_fields(front_account, data, IMAP_REQUIRED)

        dst_mailbox = data.get("archive_mailbox")
        if not dst_mailbox:
            click.echo(
                f"Error: Account '{front_account}' does not have archive_mailbox configured. "
                f"Run `weavmail mailbox --account {front_account}` to list available folders, "
                f"then `weavmail account config {front_account} --archive-mailbox <MAILBOX>` to set it.",
                err=True,
            )
            raise SystemExit(1)

        records.append((src_path, front_account, src_mailbox, uid, dst_mailbox))

    groups: dict[tuple[str, str], list[tuple[Path, str, str]]] = {}
    for src_path, account, src_mailbox, uid, dst_mailbox in records:
        key = (account, src_mailbox)
        if key not in groups:
            groups[key] = []
        groups[key].append((src_path, uid, dst_mailbox))

    for (account, src_mailbox), items in groups.items():
        data = load_account(account)
        dst_mailbox = items[0][2]

        with MailBox(data["imap_host"], port=data["imap_port"]).login(
            data["imap_username"], data["imap_password"], initial_folder=src_mailbox
        ) as mb:
            for src_path, uid, _ in items:
                mb.move(uid, dst_mailbox)

        label = "mail" if len(items) == 1 else f"{len(items)} mail(s)"
        click.echo(f"[{label} moved to archive]")
        for src_path, _, _ in items:
            click.echo(f"  file:            {src_path}")
        click.echo(f"  src mailbox:     {src_mailbox}")
        click.echo(f"  archive mailbox: {dst_mailbox}")

        click.echo(f"[syncing source mailbox: {src_mailbox}]")
        sync_mailbox(account, src_mailbox, sync_limit)
