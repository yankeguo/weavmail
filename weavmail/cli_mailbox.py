import sys

import click
from imap_tools import MailBox

from .cli import cli
from .config import load_accounts


@cli.command()
@click.option(
    "--account",
    default="default",
    show_default=True,
    help="Account name to connect with, as configured via 'weavmail account config'",
)
def mailbox(account: str):
    """List all mailbox folders for an account.

    Connects to the IMAP server and prints the name of every folder
    available in the account.
    """
    accounts = load_accounts()
    if account not in accounts:
        click.echo(f"Error: Account '{account}' not found.", err=True)
        sys.exit(1)

    data = accounts[account]
    required = ["imap_host", "imap_port", "imap_username", "imap_password"]
    missing = [p for p in required if not data.get(p)]
    if missing:
        click.echo(
            f"Error: Account '{account}' is incomplete, missing: {', '.join(missing)}",
            err=True,
        )
        sys.exit(1)

    with MailBox(data["imap_host"], port=data["imap_port"]).login(
        data["imap_username"], data["imap_password"], initial_folder=None
    ) as mb:
        for f in mb.folder.list():
            click.echo(f.name)
