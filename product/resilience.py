"""Provider-response normalization, retries, and user-safe fallbacks."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .scoring import TravelOption


@dataclass(frozen=True)
class RecoveryResult:
    """Outcome of a provider call after applying the recovery policy."""

    status: str
    attempts: int
    reason: str
    user_message: str
    options: tuple[TravelOption, ...] = ()

    @property
    def recovered(self) -> bool:
        return self.status == "success" and self.attempts > 1


def normalize_provider_payload(payload: Any) -> list[TravelOption]:
    """Validate an untrusted provider payload against the shared schema."""

    if not isinstance(payload, list):
        raise ValueError("provider payload must be a list")

    options = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("each provider option must be an object")
        try:
            options.append(
                TravelOption(
                    label=str(item["label"]),
                    price_eur=float(item["price_eur"]),
                    duration_minutes=int(item["duration_minutes"]),
                    changes=int(item.get("changes", 0)),
                    carbon_kg=(
                        None if item.get("carbon_kg") is None else float(item["carbon_kg"])
                    ),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("provider option does not match the required schema") from exc
    return options


def execute_with_recovery(
    operation: Callable[[], Any],
    *,
    max_attempts: int = 2,
) -> RecoveryResult:
    """Execute a provider call with bounded retry and explainable fallback.

    Timeouts and connection failures are retried because they are commonly
    transient. Empty or malformed responses are not retried blindly: they are
    converted into an explicit state that the UI can explain to the user.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_reason = "provider_error"
    for attempt in range(1, max_attempts + 1):
        try:
            payload = operation()
        except TimeoutError:
            last_reason = "timeout"
            if attempt < max_attempts:
                continue
            return RecoveryResult(
                status="failed",
                attempts=attempt,
                reason=last_reason,
                user_message=(
                    "The provider timed out twice. Try again later or choose another transport mode."
                ),
            )
        except ConnectionError:
            last_reason = "connection_error"
            if attempt < max_attempts:
                continue
            return RecoveryResult(
                status="failed",
                attempts=attempt,
                reason=last_reason,
                user_message=(
                    "The provider is temporarily unreachable. Your trip preferences were preserved."
                ),
            )
        except Exception:
            return RecoveryResult(
                status="failed",
                attempts=attempt,
                reason="provider_error",
                user_message="The provider returned an unexpected error. No booking action was taken.",
            )

        try:
            options = normalize_provider_payload(payload)
        except ValueError:
            return RecoveryResult(
                status="failed",
                attempts=attempt,
                reason="malformed_payload",
                user_message=(
                    "The provider response could not be validated, so it was not shown as a recommendation."
                ),
            )

        if not options:
            return RecoveryResult(
                status="no_results",
                attempts=attempt,
                reason="no_results",
                user_message=(
                    "No matching options were found. Adjust the date, budget, or transport mode and try again."
                ),
            )

        return RecoveryResult(
            status="success",
            attempts=attempt,
            reason="recovered_after_retry" if attempt > 1 else "ok",
            user_message=(
                "The provider recovered after a retry." if attempt > 1 else "Options loaded successfully."
            ),
            options=tuple(options),
        )

    raise AssertionError(f"unreachable recovery state: {last_reason}")
