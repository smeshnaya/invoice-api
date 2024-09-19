import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middlewares.utils import repeat_every
from app.config.config import settings

logger = logging.getLogger(__name__)


# rc = OrnamentRedisCluster()  # init and import if redis is necessary


@repeat_every(seconds=settings.redis_refresh_connect_interval)
async def refresh_redis_connect():
    # rc.refresh_connect()
    logger.debug("Redis connection refreshed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Usage:
    application = FastAPI(
        lifespan=lifespan,
    )
    """
    await asyncio.gather(
        refresh_redis_connect(),
    )
    yield
