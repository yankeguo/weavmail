import click

from .cli import cli


@cli.command()
@click.argument("account")
@click.argument("mailbox")
def fetch(account: str, mailbox: str):
    """Fetch mails from a mailbox"""
    pass
