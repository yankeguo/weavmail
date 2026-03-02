import re
import sys
from pathlib import Path

import click
import yaml
from imap_tools import MailBox, MailMessageFlags

from .cli import cli
from .config import load_accounts

# IMAP required fields for sync
_REQUIRED = ["imap_host", "imap_port", "imap_username", "imap_password"]


def _safe_dirname(name: str) -> str:
    """Replace characters that are unsafe in directory/file names."""
    return re.sub(r"[^\w\-.]", "_", name)


def sync_mailbox(account: str, mailbox_name: str, limit: int) -> None:
    """Core sync logic, reusable by other commands."""
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

    # Prepare output directory: ./mails/<account>_<mailbox>/
    dir_name = f"{_safe_dirname(account)}_{_safe_dirname(mailbox_name)}"
    output_dir = Path("mails") / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with MailBox(data["imap_host"], port=data["imap_port"]).login(
        data["imap_username"], data["imap_password"], initial_folder=mailbox_name
    ) as mb:
        # Collect all remote UIDs
        remote_uids = set(mb.uids())

        # Remove local files whose UID no longer exists on the server
        for local_file in output_dir.glob("*.md"):
            if local_file.stem not in remote_uids:
                local_file.unlink()
                click.echo(f"[mail deleted]\n  file: {local_file}\n")

        # Fetch latest emails (limited) and save new ones
        for msg in mb.fetch(limit=limit, reverse=True, mark_seen=False):
            uid = msg.uid
            if not uid:
                continue

            out_file = output_dir / f"{uid}.md"
            if out_file.exists():
                click.echo(
                    f"[mail already existed]\n"
                    f"  file:    {out_file}\n"
                    f"  from:    {msg.from_}\n"
                    f"  subject: {msg.subject}\n"
                )
                continue

            # Build YAML front matter
            front: dict = {
                "uid": uid,
                "account": account,
                "mailbox": mailbox_name,
                "subject": msg.subject,
                "from": msg.from_,
                "to": list(msg.to),
                "cc": list(msg.cc),
                "date": msg.date_str,
                "flags": list(msg.flags),
            }
            yaml_block = yaml.dump(front, allow_unicode=True, sort_keys=False).rstrip()
            body = msg.text or msg.html or ""

            content = f"---\n{yaml_block}\n---\n\n{body.strip()}\n"
            out_file.write_text(content, encoding="utf-8")
            mb.flag([uid], [MailMessageFlags.SEEN], True)
            click.echo(
                f"[mail saved]\n"
                f"  file:    {out_file}\n"
                f"  from:    {msg.from_}\n"
                f"  subject: {msg.subject}\n"
            )


@cli.command()
@click.option(
    "--account",
    default="default",
    show_default=True,
    help="Account name to sync, as configured via 'weavmail account config'",
)
@click.option(
    "--mailbox",
    "mailbox_name",
    default="INBOX",
    show_default=True,
    help="IMAP mailbox folder to sync, e.g. INBOX or INBOX/Sent",
)
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=int,
    help="Maximum number of most-recent emails to fetch from the server",
)
def sync(account: str, mailbox_name: str, limit: int):
    """Sync mails from an IMAP mailbox to local Markdown files.

    Fetches up to --limit most-recent messages and saves each as a .md file
    under ./mails/<account>_<mailbox>/. Files that already exist are skipped.
    Local files whose UID no longer exists on the server are deleted.
    """
    sync_mailbox(account, mailbox_name, limit)
