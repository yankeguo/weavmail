from pathlib import Path

import click
import yaml
from imap_tools import MailBox, MailMessageFlags

from .cli import cli
from .config import IMAP_REQUIRED, load_account, load_accounts, require_account_fields, safe_dirname


def sync_mailbox(account: str, mailbox_name: str, limit: int) -> None:
    """Core sync logic, reusable by other commands."""
    data = load_account(account)
    require_account_fields(account, data, IMAP_REQUIRED)

    # Prepare output directory: ./mails/<account>_<mailbox>/
    dir_name = f"{safe_dirname(account)}_{safe_dirname(mailbox_name)}"
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

        # Fetch latest emails (limited) and save them
        for msg in mb.fetch(limit=limit, reverse=True, mark_seen=False):
            uid = msg.uid
            if not uid:
                continue

            out_file = output_dir / f"{uid}.md"

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
            message_id = msg.headers.get("message-id")
            if message_id:
                front["message_id"] = message_id[0]
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
    default=None,
    help="Comma-separated account names to sync (default: all accounts)",
)
@click.option(
    "--mailbox",
    "mailbox_name",
    default="INBOX",
    show_default=True,
    help="IMAP mailbox folder to sync, e.g. INBOX",
)
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=int,
    help="Maximum number of most-recent emails to fetch",
)
def sync(account: str | None, mailbox_name: str, limit: int):
    """Sync mails from an IMAP mailbox to local Markdown files.

    Fetches up to --limit most-recent messages and saves each as a .md file
    under ./mails/<account>_<mailbox>/. Local files whose UID no longer exists
    on the server are deleted.
    """
    if account:
        accounts = [a.strip() for a in account.split(",") if a.strip()]
    else:
        accounts = list(load_accounts().keys())

    if not accounts:
        click.echo("Error: no accounts configured.", err=True)
        raise SystemExit(1)

    for acct in accounts:
        sync_mailbox(acct, mailbox_name, limit)
