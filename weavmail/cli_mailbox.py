import click
from imap_tools import MailBox

from .cli import cli
from .config import IMAP_REQUIRED, load_account, require_account_fields


@cli.command()
@click.option(
    "--account",
    default="default",
    show_default=True,
    help="Account name to connect with",
)
def mailbox(account: str):
    """List all mailbox folders for an account.

    Connects to the IMAP server and prints the name of every folder
    available in the account.
    """
    data = load_account(account)
    require_account_fields(account, data, IMAP_REQUIRED)

    with MailBox(data["imap_host"], port=data["imap_port"]).login(
        data["imap_username"], data["imap_password"], initial_folder=None
    ) as mb:
        for f in mb.folder.list():
            click.echo(f.name)
