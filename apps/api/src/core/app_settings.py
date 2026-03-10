from dataclasses import dataclass

from src.core.config import get_settings


@dataclass(frozen=True)
class AppSettings:
    name: str
    environment: str


app_settings = AppSettings(
    name=get_settings().app_name,
    environment=get_settings().app_env,
)
