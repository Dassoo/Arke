from rich.logging import RichHandler
from utils.console import console
import logging


class ThirdPartyFilter(logging.Filter):
    """Filter to block logs from third-party libraries."""

    def __init__(self, app_name: str):
        super().__init__()
        self.app_name = app_name

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self.app_name) or record.name == "__main__"


def setup_logging(
    level: int = logging.INFO,
    app_name: str = "Arke",
) -> logging.Logger:
    """Configure and return a Rich-colored logger instance."""

    handler = RichHandler(
        console=console,
        level=level,
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )

    handler.addFilter(ThirdPartyFilter(app_name))

    logger = logging.getLogger(app_name)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    return logger


logger = setup_logging()
