"""Utility class for conditional console output."""

from typing import Any
import rich


class Writer:
    """
    A utility class for conditional writing to console based on verbosity.

    This class wraps rich.print with conditional output based on a verbose flag.
    """

    def __init__(self, verbose: bool = True):
        """Initialize the writer with the verbose flag.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose

    def echo(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Echo a message if verbose mode is enabled.

        Args:
            message: The message to echo
            *args: Additional arguments to pass to rich.print
            **kwargs: Additional keyword arguments to pass to rich.print
        """
        if self.verbose:
            rich.print(message, *args, **kwargs)

    def always_echo(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Always echo a message regardless of verbose mode.

        Args:
            message: The message to echo
            *args: Additional arguments to pass to rich.print
            **kwargs: Additional keyword arguments to pass to rich.print
        """
        rich.print(message, *args, **kwargs)
