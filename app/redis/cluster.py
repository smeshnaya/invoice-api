
"""
Redis cluster module
Init manually on app startup (if necessary):
rc = OrnamentRedisCluster()
"""
import logging
from typing import Optional

from redis import RedisCluster

from app.config.config import settings
from app.redis.utils import get_startup_nodes

logger = logging.getLogger(__name__)


class OrnamentRedisCluster:
    connect: Optional[RedisCluster] = None

    def refresh_connect(self):
        if self.connect is None:
            self.create_connect()
        else:
            try:
                if not self.connect.ping():
                    self.create_connect()
            except Exception:
                self.connect = None

    def log_if_nodes_disconnected(self):
        startup_nodes = get_startup_nodes(settings.redis_cluster)

        cluster_info = self.connect.cluster_nodes()
        connected_nodes = [
            node_host
            for node_host, node_info in cluster_info.items()
            if node_info["connected"]
        ]

        if len(startup_nodes) > len(connected_nodes):
            logger.critical(
                (
                    f"Redis cluster nodes: "
                    f"connected={len(connected_nodes)} "
                    f"startup={len(startup_nodes)}"
                )
            )

    def create_connect(self):
        startup_nodes = get_startup_nodes(settings.redis_cluster)
        if not startup_nodes:
            return

        try:
            self.connect = RedisCluster(
                startup_nodes=startup_nodes, password=settings.redis_password
            )
            self.log_if_nodes_disconnected()

        except Exception as err:
            logger.critical("Redis Cluster: connection error", exc_info=err)
            self.connect = None
