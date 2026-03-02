import sys

import click

from .cli import cli
from .config import ACCOUNT_PARAMS, load_accounts, save_accounts


@cli.group("account")
def account():
    """Manage mail accounts"""
    pass


@account.command("list")
def account_list():
    """List all configured accounts"""
    accounts = load_accounts()
    if not accounts:
        click.echo("No accounts configured")
        return

    for name, data in accounts.items():
        missing = [p for p in ACCOUNT_PARAMS if not data.get(p)]
        if missing:
            click.echo(f"{name} [incomplete]")
            click.echo(f"  Warning: missing parameters: {', '.join(missing)}")
        else:
            click.echo(f"{name} [complete]")


@account.command("config")
@click.argument("name", default="default")
def account_config(name: str):
    """Create or update an account configuration"""
    accounts = load_accounts()
    existing = accounts.get(name, {})

    click.echo(f"Configuring account: {name}")
    click.echo("(Press Enter to keep the current value; leave blank to store as empty)")

    data: dict = {}

    # String parameters
    for param in [
        "imap_host",
        "imap_username",
        "imap_password",
        "smtp_host",
        "smtp_username",
        "smtp_password",
    ]:
        current = existing.get(param)
        prompt_text = f"  {param}"
        if current is not None:
            prompt_text += f" [{current}]"
        value = click.prompt(prompt_text, default="", show_default=False)
        if value == "":
            # Keep existing or store null
            data[param] = current if current is not None else None
        else:
            data[param] = value

    # Integer parameters
    for param in ["imap_port", "smtp_port"]:
        current = existing.get(param)
        prompt_text = f"  {param}"
        if current is not None:
            prompt_text += f" [{current}]"
        raw = click.prompt(prompt_text, default="", show_default=False)
        if raw == "":
            data[param] = current if current is not None else None
        else:
            try:
                data[param] = int(raw)
            except ValueError:
                click.echo(
                    f"  Warning: '{raw}' is not a valid integer; storing as null."
                )
                data[param] = None

    # Addresses (comma-separated → list)
    current_addrs = existing.get("addresses")
    if current_addrs:
        current_str = (
            ", ".join(current_addrs)
            if isinstance(current_addrs, list)
            else str(current_addrs)
        )
    else:
        current_str = None
    prompt_text = "  addresses (comma-separated)"
    if current_str is not None:
        prompt_text += f" [{current_str}]"
    raw_addrs = click.prompt(prompt_text, default="", show_default=False)
    if raw_addrs == "":
        data["addresses"] = current_addrs if current_addrs is not None else None
    else:
        data["addresses"] = [a.strip() for a in raw_addrs.split(",") if a.strip()]

    accounts[name] = data
    save_accounts(accounts)
    click.echo(f"Account '{name}' saved.")


@account.command("delete")
@click.argument("name")
def account_delete(name: str):
    """Delete an account"""
    accounts = load_accounts()
    if name not in accounts:
        click.echo(f"Error: Account '{name}' not found.", err=True)
        sys.exit(1)
    del accounts[name]
    save_accounts(accounts)
    click.echo(f"Account '{name}' deleted.")
