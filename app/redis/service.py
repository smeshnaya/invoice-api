
from redis.cluster import RedisCluster
from redis.exceptions import RedisError

from app.config.config import settings


class RedisService:
    def __init__(
        self,
        redis_connection: RedisCluster,
        stream_prefix: str,
        ttl_sec: int,
    ):
        self.ttl_sec = ttl_sec
        self.group_name = settings.service_name

        self.redis_connection = redis_connection
        self.stream_name = (
            f"{settings.environment.value}:{self.group_name}:{stream_prefix}"
        )

        try:
            self.redis_connection.xgroup_create(
                name=self.stream_name,
                groupname=self.group_name,
                mkstream=True,
            )
        except RedisError:
            pass

    def publish(self, key: str, value: str):
        self.redis_connection.set(
            f"{self.stream_name}:{key}",
            value,
            ex=self.ttl_sec,
        )

    def get(self, key: str):
        return self.redis_connection.get(f"{self.stream_name}:{key}")
