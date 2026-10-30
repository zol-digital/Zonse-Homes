"""Provider-independent email delivery contract and safe default implementation."""

import logging
from dataclasses import dataclass
from typing import Protocol

from app.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when an email cannot be delivered."""


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    body: str


class EmailDelivery(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def send(self, message: EmailMessage) -> None: ...


class UnconfiguredEmailDelivery:
    @property
    def is_configured(self) -> bool:
        return False

    def send(self, message: EmailMessage) -> None:
        del message
        raise EmailDeliveryError("Email delivery has not been configured")


class MemoryEmailDelivery:
    """In-memory adapter for tests; never register this adapter in production."""

    def __init__(self) -> None:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("Memory email delivery is unavailable in production")
        self.messages: list[EmailMessage] = []

    @property
    def is_configured(self) -> bool:
        return True

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


_unconfigured_delivery = UnconfiguredEmailDelivery()


def get_email_delivery() -> EmailDelivery:
    """Return the safe default until a deployment supplies a provider adapter."""
    return _unconfigured_delivery


def deliver_email_message(delivery: EmailDelivery, message: EmailMessage) -> None:
    try:
        delivery.send(message)
    except EmailDeliveryError:
        logger.error("Account email delivery failed")
