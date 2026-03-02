import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

import click
import yaml

from .cli import cli
from .config import load_accounts

_REQUIRED_SMTP = ["smtp_host", "smtp_port", "smtp_username", "smtp_password"]

# Max lines of quoted original mail body (100 before + 100 after = up to 200 lines)
_QUOTE_LINES = 100


def _parse_front_matter(path: Path) -> tuple[dict, str]:
    """Parse YAML front matter and body from a .md file."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("file has no YAML front matter")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed YAML front matter")
    return yaml.safe_load(parts[1]), parts[2].strip()


def _quote_body(body: str) -> str:
    """Trim body to at most _QUOTE_LINES*2 lines and prefix each line with '> '."""
    lines = body.splitlines()
    if len(lines) > _QUOTE_LINES * 2:
        lines = lines[:_QUOTE_LINES] + ["... (trimmed) ..."] + lines[-_QUOTE_LINES:]
    return "\n".join(f"> {line}" for line in lines)


def _subject_with_re_prefix(subject: str) -> str:
    if subject.lower().startswith("re:"):
        return subject
    return f"Re: {subject}"


@cli.command()
@click.option("--account", default="default", show_default=True, help="Account name")
@click.option(
    "--from",
    "from_addr",
    default=None,
    help="Sender address (defaults to first configured address)",
)
@click.option(
    "--to", "to_addrs", multiple=True, help="Recipient address(es), repeatable"
)
@click.option("--subject", default=None, help="Mail subject")
@click.option(
    "--content",
    "content_file",
    default=None,
    type=click.Path(exists=True),
    help="File containing mail body",
)
@click.option(
    "--reply",
    "reply_file",
    default=None,
    type=click.Path(exists=True),
    help="Local .md file to reply to",
)
def send(account: str, from_addr, to_addrs, subject, content_file, reply_file):
    """Send a mail or reply to an existing mail.

    Basic send:   --to addr --subject "Hello" --content body.txt\n
    Reply:        --reply mails/default_INBOX/123.md --content reply.txt
    """
    accounts = load_accounts()
    if account not in accounts:
        click.echo(f"Error: Account '{account}' not found.", err=True)
        sys.exit(1)

    data = accounts[account]
    missing = [p for p in _REQUIRED_SMTP if not data.get(p)]
    if missing:
        click.echo(
            f"Error: Account '{account}' is incomplete, missing: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)

    # Resolve sender address
    configured_addresses = data.get("addresses") or []
    if from_addr is None:
        if not configured_addresses:
            click.echo(
                "Error: no --from specified and no addresses configured for account.",
                err=True,
            )
            sys.exit(1)
        from_addr = configured_addresses[0]

    # Load content body
    if content_file is None:
        click.echo("Error: --content is required.", err=True)
        sys.exit(1)
    body = Path(content_file).read_text(encoding="utf-8").strip()

    # Reply mode
    reply_front: dict | None = None
    reply_body_quoted = ""
    if reply_file is not None:
        try:
            reply_front, original_body = _parse_front_matter(Path(reply_file))
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        # Fill in subject and to from original mail if not provided
        if subject is None:
            subject = _subject_with_re_prefix(reply_front.get("subject") or "")
        if not to_addrs:
            original_from = reply_front.get("from")
            if original_from:
                to_addrs = (original_from,)

        # Infer from_addr from the original mail's to/cc if not explicitly provided
        if from_addr == configured_addresses[0]:
            original_to = reply_front.get("to") or []
            original_cc = reply_front.get("cc") or []
            for addr in list(original_to) + list(original_cc):
                if addr in configured_addresses:
                    from_addr = addr
                    break

        reply_body_quoted = _quote_body(original_body)

    # Validate that from_addr is one of the configured addresses
    if from_addr not in configured_addresses:
        click.echo(
            f"Error: sender '{from_addr}' is not in the configured addresses for account '{account}'.\n"
            f"  Configured: {', '.join(configured_addresses)}",
            err=True,
        )
        sys.exit(1)

    # Validate required fields
    if not to_addrs:
        click.echo("Error: at least one --to address is required.", err=True)
        sys.exit(1)
    if not subject:
        click.echo(
            "Error: --subject is required (or use --reply to infer it).", err=True
        )
        sys.exit(1)

    # Compose final body: new content first, then quoted original
    if reply_body_quoted:
        full_body = f"{body}\n\n{reply_body_quoted}"
    else:
        full_body = body

    # Build email message
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(full_body)

    # Set reply headers if replying
    if reply_front is not None:
        original_headers = reply_front.get("headers") or {}
        message_id = original_headers.get("message-id") or original_headers.get(
            "Message-ID"
        )
        if isinstance(message_id, (list, tuple)):
            message_id = message_id[0]
        if message_id:
            msg["In-Reply-To"] = message_id
            msg["References"] = message_id

    # Send via SMTP over TLS
    with smtplib.SMTP_SSL(data["smtp_host"], port=data["smtp_port"]) as smtp:
        smtp.login(data["smtp_username"], data["smtp_password"])
        smtp.send_message(msg)

    click.echo(
        f"[mail sent]\n"
        f"  from:    {from_addr}\n"
        f"  to:      {', '.join(to_addrs)}\n"
        f"  subject: {subject}\n"
    )
