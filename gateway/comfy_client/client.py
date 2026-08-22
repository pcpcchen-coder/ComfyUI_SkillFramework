from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import requests

from gateway.errors import BackendUnavailableError, ExecutionFailedError, InvalidInputError


class ComfyClient:
    """Small client for the stable local ComfyUI server API surface.

    P1 intentionally uses HTTP polling instead of browser automation. WebSocket
    progress streaming can be layered on later without changing skill contracts.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        *,
        timeout: float = 30.0,
        client_id: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = client_id or uuid.uuid4().hex
        self.session = session or requests.Session()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise BackendUnavailableError(
                f"ComfyUI request failed: {method} {path}",
                details={"reason": str(exc), "base_url": self.base_url},
            ) from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/system_stats").json()

    def upload_input(
        self,
        file_path: str | Path,
        *,
        subfolder: str = "agent-skills",
        overwrite: bool = False,
    ) -> str:
        path = Path(file_path)
        if not path.is_file():
            raise InvalidInputError(f"Input file does not exist: {path}")

        # ComfyUI's legacy /upload/image route stores uploaded bytes in the
        # selected input directory. Despite the route name, the server-side
        # generic upload path is useful for loader nodes that consume files
        # from ComfyUI's input directory, including video loader extensions.
        with path.open("rb") as handle:
            response = self._request(
                "POST",
                "/upload/image",
                files={"image": (path.name, handle)},
                data={
                    "type": "input",
                    "subfolder": subfolder,
                    "overwrite": "true" if overwrite else "false",
                },
            )

        payload = response.json()
        name = payload.get("name")
        returned_subfolder = payload.get("subfolder", "")
        if not name:
            raise ExecutionFailedError(
                "ComfyUI upload response did not contain a file name.",
                details={"response": payload},
            )
        return f"{returned_subfolder}/{name}" if returned_subfolder else str(name)

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        response = self._request("POST", "/prompt", json=payload).json()
        prompt_id = response.get("prompt_id")
        if not prompt_id:
            raise ExecutionFailedError(
                "ComfyUI did not return a prompt_id.",
                details={"response": response},
            )
        return str(prompt_id)

    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        payload = self._request("GET", f"/history/{prompt_id}").json()
        entry = payload.get(prompt_id)
        return entry if isinstance(entry, dict) else None

    def wait_for_completion(
        self,
        prompt_id: str,
        *,
        timeout_seconds: float = 3600,
        poll_interval: float = 1.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            history = self.get_history(prompt_id)
            if history is not None:
                status = history.get("status", {})
                status_str = status.get("status_str") if isinstance(status, dict) else None
                if status_str == "error":
                    raise ExecutionFailedError(
                        "ComfyUI workflow execution failed.",
                        details={"prompt_id": prompt_id, "status": status},
                    )
                # Completed history entries contain outputs. Some custom nodes
                # may legitimately produce an empty outputs object, so history
                # presence + a completed status is the primary signal.
                if status_str in {"success", "completed"} or history.get("outputs"):
                    return history
            time.sleep(poll_interval)

        raise ExecutionFailedError(
            "Timed out waiting for ComfyUI workflow completion.",
            details={"prompt_id": prompt_id, "timeout_seconds": timeout_seconds},
        )
