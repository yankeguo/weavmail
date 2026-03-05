import smtplib
from email.message import EmailMessage
from pathlib import Path

import click
from imap_tools import MailBox, MailMessageFlags

from .cli import cli
from .config import (
    IMAP_REQUIRED,
    SMTP_REQUIRED,
    load_account,
    parse_front_matter,
    require_account_fields,
)

# Max lines of quoted original mail body kept per side (head + tail)
_QUOTE_LINES = 100


def _quote_body(body: str) -> str:
    """Trim body to at most _QUOTE_LINES*2 lines and prefix each line with '> '."""
    lines = body.splitlines()
    if len(lines) > _QUOTE_LINES * 2:
        lines = lines[:_QUOTE_LINES] + ["... (trimmed) ..."] + lines[-_QUOTE_LINES:]
    return "\n".join(f"> {line}" for line in lines)


def _reply_subject(subject: str) -> str:
    if subject.lower().startswith("re:"):
        return subject
    return f"Re: {subject}"


@cli.command()
@click.option(
    "--account",
    default="default",
    show_default=True,
    help="Account name; when using --reply, must match the account in the mail's front matter",
)
@click.option(
    "--from",
    "from_addr",
    default=None,
    help="Sender address (defaults to first configured address)",
)
@click.option(
    "--to", "to_addrs", multiple=True, help="Recipient address(es), repeatable"
)
@click.option("--cc", "cc_addrs", multiple=True, help="CC address(es), repeatable")
@click.option("--bcc", "bcc_addrs", multiple=True, help="BCC address(es), repeatable")
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
@click.option(
    "--no-save-sent",
    is_flag=True,
    default=False,
    help="Skip saving sent mail to the Sent mailbox (use for providers that auto-save, e.g. Gmail)",
)
def send(
    account: str,
    from_addr,
    to_addrs,
    cc_addrs,
    bcc_addrs,
    subject,
    content_file,
    reply_file,
    no_save_sent,
):
    """Send a mail or reply to an existing mail.

    Basic send:   --to addr --subject "Hello" --content body.txt\n
    Reply:        --reply mails/default_INBOX/123.md --content reply.txt

    After sending, the mail is appended to the Sent mailbox via IMAP unless
    --no-save-sent is set or sent_mailbox is not configured.
    """
    data = load_account(account)
    require_account_fields(account, data, SMTP_REQUIRED)

    configured_addresses: list = data.get("addresses") or []

    # Resolve default sender address
    if from_addr is None:
        if not configured_addresses:
            click.echo(
                "Error: no --from specified and no addresses configured for account.",
                err=True,
            )
            raise SystemExit(1)
        from_addr = configured_addresses[0]

    # Load content body
    if content_file is None:
        click.echo("Error: --content is required.", err=True)
        raise SystemExit(1)
    body = Path(content_file).read_text(encoding="utf-8").strip()

    # Reply mode: infer subject, to, from, and quote original body
    reply_front: dict | None = None
    reply_body_quoted = ""
    if reply_file is not None:
        reply_front, original_body = parse_front_matter(Path(reply_file))

        # Validate account matches front matter
        reply_account = reply_front.get("account")
        if reply_account and reply_account != account:
            click.echo(
                f"Error: --account '{account}' does not match the reply file's front matter account '{reply_account}'.",
                err=True,
            )
            raise SystemExit(1)

        if subject is None:
            subject = _reply_subject(reply_front.get("subject") or "")

        if not to_addrs:
            original_from = reply_front.get("from")
            if original_from:
                to_addrs = (original_from,)

        # Pick from_addr from the original mail's to/cc if it matches a configured address
        if from_addr == configured_addresses[0]:
            for addr in list(reply_front.get("to") or []) + list(
                reply_front.get("cc") or []
            ):
                if addr in configured_addresses:
                    from_addr = addr
                    break

        reply_body_quoted = _quote_body(original_body)

    # Validate sender is a configured address
    if configured_addresses and from_addr not in configured_addresses:
        click.echo(
            f"Error: sender '{from_addr}' is not in the configured addresses for account '{account}'.\n"
            f"  Configured: {', '.join(configured_addresses)}",
            err=True,
        )
        raise SystemExit(1)

    if not to_addrs:
        click.echo("Error: at least one --to address is required.", err=True)
        raise SystemExit(1)
    if not subject:
        click.echo(
            "Error: --subject is required (or use --reply to infer it).", err=True
        )
        raise SystemExit(1)

    # Compose final body
    full_body = f"{body}\n\n{reply_body_quoted}" if reply_body_quoted else body

    # Build email message
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    if bcc_addrs:
        msg["Bcc"] = ", ".join(bcc_addrs)
    msg["Subject"] = subject
    msg.set_content(full_body)

    # Set reply headers
    if reply_front is not None:
        message_id = reply_front.get("message_id")
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
        + (f"  cc:      {', '.join(cc_addrs)}\n" if cc_addrs else "")
        + (f"  bcc:     {', '.join(bcc_addrs)}\n" if bcc_addrs else "")
        + f"  subject: {subject}\n"
    )

    # Append to Sent mailbox via IMAP unless disabled
    if not no_save_sent:
        target_sent = data.get("sent_mailbox")
        if not target_sent:
            click.echo(
                f"Error: Account '{account}' does not have sent_mailbox configured. "
                f"Run `weavmail mailbox --account {account}` to list available folders, "
                f"then `weavmail account config {account} --sent-mailbox <MAILBOX>` to set it, "
                f"or pass --no-save-sent to skip saving.",
                err=True,
            )
            raise SystemExit(1)
        require_account_fields(account, data, IMAP_REQUIRED)
        with MailBox(data["imap_host"], port=data["imap_port"]).login(
            data["imap_username"], data["imap_password"], initial_folder=None
        ) as mb:
            mb.append(
                msg.as_bytes(), target_sent, flag_set=[MailMessageFlags.SEEN]
            )
        click.echo(f"[mail saved to sent]\n  mailbox: {target_sent}\n")
