from . import cli_account  # noqa: F401 - imports for side effects (register commands)
from . import cli_mailbox  # noqa: F401 - imports for side effects (register commands)
from . import cli_move  # noqa: F401 - imports for side effects (register commands)
from . import cli_send  # noqa: F401 - imports for side effects (register commands)
from . import cli_sync  # noqa: F401 - imports for side effects (register commands)
from .cli import cli

__all__ = ["cli"]
