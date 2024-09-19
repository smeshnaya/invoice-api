import logging

import sentry_sdk

from app.config.config import settings
from app.config.environment import Environment

logger = logging.getLogger(__name__)


def init_sentry():
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.environment.value,
        before_send=before_send,
        traces_sampler=lambda context: settings.sentry_traces_sample_rate,
        send_default_pii=True,
        release=settings.version,
        profiles_sample_rate=settings.sentry_profiling_sample_rate,
    )


def before_send(event, hint):
    if event["environment"] == Environment.local.value:
        logger.debug(f"Sentry log skipped for event: \n {event}")
        return None

    return event
