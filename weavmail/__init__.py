from . import (
    cli_account,  # noqa: F401 - imports for side effects (register commands)
    cli_archive,  # noqa: F401 - imports for side effects (register commands)
    cli_mailbox,  # noqa: F401 - imports for side effects (register commands)
    cli_move,  # noqa: F401 - imports for side effects (register commands)
    cli_send,  # noqa: F401 - imports for side effects (register commands)
    cli_sync,  # noqa: F401 - imports for side effects (register commands)
    cli_trash,  # noqa: F401 - imports for side effects (register commands)
)
from .cli import cli

__all__ = ["cli"]
