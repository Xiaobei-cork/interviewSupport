import logging
import sys
from pathlib import Path


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    app_logger.addHandler(console)

    file_handler = logging.FileHandler(
        Path(log_dir) / "app.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    access_logger = logging.getLogger("app.access")
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()
    access_logger.addHandler(console)
    access_logger.addHandler(
        logging.FileHandler(Path(log_dir) / "access.log", encoding="utf-8")
    )
    for h in access_logger.handlers:
        h.setFormatter(formatter)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    app_logger.info("日志模块初始化完成")
    return app_logger
