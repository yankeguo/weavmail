import click

from .cli import cli


@cli.command()
@click.argument("account")
@click.argument("mailbox")
def delete(account: str, mailbox: str):
    """Delete mails from a mailbox"""
    pass
