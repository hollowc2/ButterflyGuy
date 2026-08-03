"""Opt-in client configuration; direct access remains the safe default."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewayClientSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    access_mode: Literal["direct", "gateway"] = Field(
        default="direct",
        validation_alias="SCHWAB_ACCESS_MODE",
    )
    gateway_url: str = Field(
        default="",
        validation_alias="SCHWAB_GATEWAY_URL",
    )
    gateway_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="SCHWAB_GATEWAY_API_KEY",
    )

    @model_validator(mode="after")
    def gateway_mode_requires_connection_settings(self) -> GatewayClientSettings:
        if self.access_mode == "gateway" and (
            not self.gateway_url or not self.gateway_api_key.get_secret_value()
        ):
            raise ValueError("gateway mode requires SCHWAB_GATEWAY_URL and API key")
        return self
