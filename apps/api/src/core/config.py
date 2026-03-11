from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Sinai Lead Intake API'
    app_env: str = Field(..., alias='APP_ENV')
    database_url: str = Field(..., alias='DATABASE_URL')
    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')
    default_agency_id: str = Field('default', alias='DEFAULT_AGENCY_ID')

    # RingCentral — all optional; empty string means "not configured"
    ringcentral_client_id: str = Field('', alias='RINGCENTRAL_CLIENT_ID')
    ringcentral_client_secret: str = Field('', alias='RINGCENTRAL_CLIENT_SECRET')
    ringcentral_jwt_token: str = Field('', alias='RINGCENTRAL_JWT_TOKEN')
    ringcentral_from_number: str = Field('', alias='RINGCENTRAL_FROM_NUMBER')
    ringcentral_webhook_verification_token: str = Field('', alias='RINGCENTRAL_WEBHOOK_VERIFICATION_TOKEN')
    ringcentral_webhook_url: str = Field('', alias='RINGCENTRAL_WEBHOOK_URL')
    ringcentral_subscription_id: str | None = Field(None, alias='RINGCENTRAL_SUBSCRIPTION_ID')


@lru_cache

def get_settings() -> Settings:
    return Settings()
