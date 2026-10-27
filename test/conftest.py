import logging
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def reset_masha_logging() -> Iterator[None]:
    """Undo configure_logging() so tests do not leak handlers or levels.

    The CLI binds a handler to the stderr stream that CliRunner swaps in;
    reusing it in a later test would write to a closed stream. It also
    disables propagation, which would hide records from ``caplog``.
    """
    yield
    package_logger = logging.getLogger("masha")
    for handler in list(package_logger.handlers):
        package_logger.removeHandler(handler)
    package_logger.setLevel(logging.NOTSET)
    package_logger.propagate = True
