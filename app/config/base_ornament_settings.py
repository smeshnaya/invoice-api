from pydantic import Field
from pydantic_settings import BaseSettings

from app.config.environment import Environment

environment_alias = "CIRCUIT_SNAME"


class OrnamentBaseSettings(BaseSettings):
    service_name: str
    port: int = 5000

    environment: Environment = Field(..., alias=environment_alias)

    slack_api_token: str
    slack_timeout: int = Field(default=1, title="Timeout seconds")
    slack_channel: str

    # Sentry
    sentry_dsn: str
    sentry_traces_sample_rate: float = 1.0
    sentry_profiling_sample_rate: float = 1.0

    # Redis
    redis_cluster: str
    redis_password: str | None = None
    redis_refresh_connect_interval: int = 600
    redis_default_expire: int = 600
    redis_expire_get_profile_has_nonvitals: int = 15
    redis_expire_get_profile_reference_ranges: int = 86400

    # Swagger
    swagger_public_api_url: str
    swagger_internal_api_url: str

    version: str
