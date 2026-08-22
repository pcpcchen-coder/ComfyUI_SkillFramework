from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GatewayError(Exception):
    code: str
    message: str
    retryable: bool = False
    suggested_action: str | None = None
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.suggested_action:
            payload["suggested_action"] = self.suggested_action
        if self.details:
            payload["details"] = self.details
        return payload


class InvalidInputError(GatewayError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__("INVALID_INPUT", message, False, None, details)


class WorkflowValidationError(GatewayError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__("WORKFLOW_VALIDATION_FAILED", message, False, None, details)


class BackendUnavailableError(GatewayError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(
            "BACKEND_UNAVAILABLE",
            message,
            True,
            "retry_or_switch_backend",
            details,
        )


class ExecutionFailedError(GatewayError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__("EXECUTION_FAILED", message, False, None, details)


class OutputNotFoundError(GatewayError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__("OUTPUT_NOT_FOUND", message, False, None, details)
