import os

from app.config.base_ornament_settings import OrnamentBaseSettings, environment_alias
from app.config.environment import Environment
from app.exceptions.settings_exceptions import SettingsException


class Settings(OrnamentBaseSettings):
    """Project settings."""

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


# получаем окружение. Если окружение - local, то используем .env.local файл
environment = os.getenv(environment_alias)
if not environment or environment == Environment.local.value:
    settings = Settings()
elif (
    environment == Environment.development.value
    or environment == Environment.testing.value
    or environment == Environment.production.value
    or environment == Environment.stage.value
):
    settings = Settings()
else:
    raise SettingsException(f"Incorrect {environment_alias} value {environment}")
