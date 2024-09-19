import logging
from logging.handlers import TimedRotatingFileHandler

import uvicorn

from app.config.config import settings
from app.config.environment import Environment

# Uvicorn settings
workers = 2
keep_alive = 20
timeout = 30
graceful_timeout = 15
backlog = workers * 50  # Adjust the backlog value as needed

# Logging configuration
log_format = "%(asctime)s [%(process)d] [%(levelname)s] %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)

# Create handlers for error and access logs
if settings.environment == Environment.local:
    error_handler = TimedRotatingFileHandler(
        "./app/datadir/logs/error.log", when="midnight", backupCount=7
    )
    access_handler = TimedRotatingFileHandler(
        "./app/datadir/logs/access.log", when="midnight", backupCount=7
    )
else:
    error_handler = TimedRotatingFileHandler(
        "/app/datadir/logs/error.log", when="midnight", backupCount=7
    )
    access_handler = TimedRotatingFileHandler(
        "/app/datadir/logs/access.log", when="midnight", backupCount=7
    )

error_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
access_handler.setFormatter(
    logging.Formatter("%(asctime)s %(message)s", datefmt=date_format)
)

error_logger = logging.getLogger("uvicorn.error")
access_logger = logging.getLogger("uvicorn.access")

error_logger.addHandler(error_handler)
access_logger.addHandler(access_handler)

port = settings.port

if settings.environment == Environment.local:
    app_reload = True
    workers = 1
else:
    app_reload = False

if __name__ == "__main__":
    uvicorn.run(
        "app.application:application",
        host="0.0.0.0",
        port=port,
        workers=workers,
        backlog=backlog,  # Set the desired backlog value
        reload=app_reload,  # You can set this to True during development for automatic reloading
        log_config=None,  # Use default logging configuration
        timeout_keep_alive=keep_alive,
    )
