from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gateway.comfy_client.client import ComfyClient
from gateway.workflow import Binding, load_workflow, patch_workflow


@dataclass(slots=True)
class RunResult:
    prompt_id: str
    history: dict[str, Any]
    uploaded_inputs: dict[str, str]


def run_workflow(
    *,
    client: ComfyClient,
    workflow_path: str | Path,
    bindings: dict[str, Binding],
    file_inputs: dict[str, str | Path],
    literal_inputs: dict[str, Any] | None = None,
    timeout_seconds: float = 3600,
) -> RunResult:
    workflow = load_workflow(workflow_path)

    uploaded: dict[str, str] = {}
    for name, file_path in file_inputs.items():
        uploaded[name] = client.upload_input(file_path)

    values: dict[str, Any] = dict(uploaded)
    if literal_inputs:
        values.update(literal_inputs)

    patched = patch_workflow(workflow, bindings, values)
    prompt_id = client.queue_prompt(patched)
    history = client.wait_for_completion(prompt_id, timeout_seconds=timeout_seconds)

    return RunResult(
        prompt_id=prompt_id,
        history=history,
        uploaded_inputs=uploaded,
    )


def collect_output_files(history: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten common ComfyUI output descriptors from history.

    Supports images/gifs/videos-style output lists without depending on a
    particular custom node package. Unknown output structures are ignored.
    """
    found: list[dict[str, Any]] = []
    outputs = history.get("outputs", {})
    if not isinstance(outputs, dict):
        return found

    for node_id, node_output in outputs.items():
        if not isinstance(node_output, dict):
            continue
        for key, value in node_output.items():
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, dict) and "filename" in item:
                    found.append({"node_id": str(node_id), "kind": key, **item})
    return found
