"""Logging setup used by the command-line application."""

import logging


def configure_logging(verbose: bool = False) -> None:
    """Configure readable console logging once for the application."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
