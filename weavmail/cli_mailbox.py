import click

from .cli import cli


@cli.command()
@click.argument("account")
def mailbox(account: str):
    """List mailboxes for an account"""
    pass
