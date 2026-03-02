import click

from .cli import cli


@cli.command()
@click.argument("account")
def send(account: str):
    """Send a mail via an account"""
    pass
