"""Pydantic schemas for the push-alert API (Phase 10, D-02)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SubscribeRequest(BaseModel):
    """Register a device token against alert topics."""

    token: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Device registration token (echoed back as last-6 suffix only).",
        examples=["device-token-abc123"],
    )
    topics: List[str] = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Alert topics to subscribe (FCM charset, max 128 chars each).",
        examples=[["alerts-mumbai"]],
    )


class SendRequest(BaseModel):
    """Direct-send payload: exactly one of token or topic, Orange/Red only."""

    token: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Device registration token (exactly one of token/topic).",
        examples=["device-token-abc123"],
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=900,
        description="FCM topic name (exactly one of token/topic).",
        examples=["alerts-mumbai"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Notification title.",
        examples=["WeatherGPT Orange alert for Mumbai"],
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Notification body.",
        examples=["Rough weather near Mumbai (non-IMD model estimate). Stay alert."],
    )
    alert_level: str = Field(
        ...,
        description="Severity label: only Orange or Red may be pushed.",
        examples=["Orange"],
    )
    location: str = Field(
        default="Mumbai",
        max_length=120,
        description="Human location label echoed in the FCM data payload.",
        examples=["Mumbai"],
    )


class CheckResponse(BaseModel):
    """Hourly cron-target report from run_watch_cycle."""

    checked: int = Field(..., description="Cities evaluated (always 18).")
    dispatched: list = Field(
        default_factory=list, description="Per-city dispatched entries."
    )
    skipped: list = Field(
        default_factory=list, description="Per-city skipped entries with reasons."
    )


class StatusResponse(BaseModel):
    """Operability snapshot: counts plus config flag, zero token bytes."""

    watch_cities: int = Field(..., description="Watched city count (always 18).")
    cooldown_hours: int = Field(..., description="Dedup cooldown in hours (always 6).")
    tokens: int = Field(..., description="Registered device-token count.")
    topics: int = Field(..., description="Topic count with at least one subscriber.")
    subscriptions: int = Field(..., description="Total token-topic subscriptions.")
    fcm_configured: bool = Field(
        ..., description="True when a service-account file loads."
    )
