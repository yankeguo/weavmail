from . import cli_account  # noqa: F401 - imports for side effects (register commands)
from . import cli_delete  # noqa: F401 - imports for side effects (register commands)
from . import cli_fetch  # noqa: F401 - imports for side effects (register commands)
from . import cli_mailbox  # noqa: F401 - imports for side effects (register commands)
from . import cli_send  # noqa: F401 - imports for side effects (register commands)
from .cli import cli

__all__ = ["cli"]
