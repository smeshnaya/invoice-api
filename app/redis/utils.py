import hashlib
import json
import logging
import re
import zlib
from contextlib import suppress
from functools import wraps
from typing import Any

from fastapi import BackgroundTasks, Request
from pydantic import BaseModel
from redis.cluster import ClusterNode, RedisCluster
from sqlalchemy.engine.row import Row

from app.config.config import settings
from app.schemas.base import OrnamentBase
from app.slack.client import SlackClient

logger = logging.getLogger(__name__)

NODE_IPV4_PATTERN = re.compile(r"\d+.\d+.\d+.\d+\s*:\s*\d+")
EXCLUDE_HOST_NODE_PATTERN = re.compile(r"\d+.\d+.\d+.\d+\s*:\s*")
EXCLUDE_PORT_NODE_PATTERN = re.compile(r"\s*:\s*\d+")


def get_startup_nodes(nodes: str):
    return [
        ClusterNode(
            EXCLUDE_PORT_NODE_PATTERN.sub("", node),
            int(EXCLUDE_HOST_NODE_PATTERN.sub("", node)),
        )
        for node in NODE_IPV4_PATTERN.findall(nodes)
    ]


def is_ornament_model_instance(data):
    return issubclass(type(data), OrnamentBase) or issubclass(type(data), BaseModel)


def set_redis_cache(rc: RedisCluster, key: str, data, exp: int):
    if isinstance(data, Row):
        data = json.dumps(tuple(data))
    elif is_ornament_model_instance(data):
        data = data.json()
    elif isinstance(data, list) and data and isinstance(data[0], Row):
        data = json.dumps([tuple(v) for v in data])
    elif isinstance(data, list) and data and (is_ornament_model_instance(data[0])):
        data = json.dumps([json.loads(v.json()) for v in data])
    else:
        data = json.dumps(data)
    compressed_data = zlib.compress(bytes(data, "utf-8"), zlib.Z_BEST_COMPRESSION)
    rc.set(key, compressed_data, exp)


def redis_cache_api(
    expire: int = settings.redis_default_expire, blacklist_body_keys: list[str] = None
):
    """cache api responses decorator"""

    if not blacklist_body_keys:
        blacklist_body_keys = []

    def decorate(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            background_tasks: BackgroundTasks = kwargs.get("background_tasks")
            redis_connect: RedisCluster = request.state.redis_connect

            no_cache = request.headers.get("cache-control") == "no-cache"
            path = request.scope.get("path")
            qp = request._query_params._dict
            _body = request.__dict__.get("_body", b"{}")
            body = json.loads(_body)
            for key in blacklist_body_keys:
                with suppress(KeyError):
                    del body[key]
            body = bytes(json.dumps(body), "utf-8")

            h = hashlib.sha256(str(path).encode() + str(qp).encode() + body).hexdigest()
            cache_key = (
                f"{settings.environment.value}:{settings.service_name}:cache:{h}"
            )

            cache = redis_connect.get(cache_key) if redis_connect else None
            if cache is None or no_cache:
                header_no_cache_msg = (
                    f"cache-control: no-cache has been detected for {path}"
                )
                not_cached_msg = f"{path} with hash {h} is not cached"
                logger.debug(f"{header_no_cache_msg if no_cache else not_cached_msg}")
                cache = await fn(*args, **kwargs)
                if len(str(cache)) and redis_connect:
                    background_tasks.add_task(
                        set_redis_cache,
                        redis_connect,
                        cache_key,
                        cache,
                        expire,
                    )
                return cache
            else:
                logger.debug(f"{path} with hash {h} is cached")
                return json.loads(zlib.decompress(cache))

        return wrapper

    return decorate


def redis_cache(
    expire: int = settings.redis_default_expire,
    cache_keys: list[str] = [],
    skip_cache_keys: list[str] = [],
    model: Any | None = None,
    list_model: Any | None = None,
):
    """cache functions"""

    def decorate(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            background_tasks: BackgroundTasks = kwargs.get("background_tasks")
            redis_connect: RedisCluster = kwargs.get("redis_connect")
            slack_client: SlackClient = SlackClient()
            cache_path: str = fn.__name__

            if any([kwargs.get(k) for k in skip_cache_keys]):
                return await fn(*args, **kwargs)

            for key in cache_keys:
                cache_path += f":{str(kwargs.get(key))}"

            h = hashlib.sha256(cache_path.encode()).hexdigest()
            cache_key = (
                f"{settings.environment.value}:{settings.service_name}:cache:{h}"
            )

            cache = redis_connect.get(cache_key) if redis_connect else None
            if cache is None:
                logger.debug(f"{cache_path} with hash {h} is not cached")
                cache = await fn(*args, **kwargs)
                if len(str(cache)) and redis_connect and background_tasks:
                    background_tasks.add_task(
                        set_redis_cache,
                        redis_connect,
                        cache_key,
                        cache,
                        expire,
                    )
                return cache

            logger.debug(f"{cache_path} with hash {h} is cached")

            data = json.loads(zlib.decompress(cache))

            if model:
                try:
                    data = model.parse_obj(data)
                except Exception:
                    return data

            if list_model:
                try:
                    data = [list_model.parse_obj(d) for d in data]
                except Exception as e:
                    await slack_client.send_async(
                        message=f"Redis cache error: {str(e)}",
                        channel=settings.slack_channel,
                        to_mention=True,
                        is_error=True,
                    )
                    logger.error(e)
                    return data

            return data

        return wrapper

    return decorate