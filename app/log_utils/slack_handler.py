import logging

from app.config.config import settings
from app.slack.client import SlackClient


class SlackHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slack_client = SlackClient()

    def emit(self, record):
        try:
            message = self.format(record)
            self.slack_client.send(
                message=message,
                channel=settings.slack_channel,
                to_mention=True,
                is_error=True,
            )
        except Exception:
            self.handleError(record)


if __name__ == "__main__":
    """
    Example code to test SlackHandler locally
    """

    # test_logger = logging.getLogger("main_logger")
    #
    # formatter = logging.Formatter(
    #     "[%(asctime)s]%(levelname)-8s%(message)s#%(filename)s[LINE:%(lineno)d]"
    # )
    #
    # slack_handler = SlackHandler()
    # slack_handler.setLevel(logging.CRITICAL)
    # slack_handler.setFormatter(formatter)
    #
    # test_logger.addHandler(slack_handler)
    #
    # test_logger.critical("Some error!")
