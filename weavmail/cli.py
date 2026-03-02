import click


@click.group()
def cli():
    """weavmail - a command line mail client"""
    pass


# ---------------------------------------------------------------------------
# mailbox
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("account")
def mailbox(account: str):
    """List mailboxes for an account"""
    pass


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("account")
@click.argument("mailbox")
def fetch(account: str, mailbox: str):
    """Fetch mails from a mailbox"""
    pass


# ---------------------------------------------------------------------------
# move
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("account")
@click.argument("src_mailbox")
@click.argument("dst_mailbox")
def move(account: str, src_mailbox: str, dst_mailbox: str):
    """Move mails between mailboxes"""
    pass


# ---------------------------------------------------------------------------
# send
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("account")
def send(account: str):
    """Send a mail via an account"""
    pass
