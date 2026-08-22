from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from gateway.comfy_client.client import ComfyClient
from gateway.errors import InvalidInputError, OutputNotFoundError
from gateway.runner import collect_output_files, run_workflow
from gateway.workflow import Binding

SKILL_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = SKILL_DIR / "skill.yaml"


def _load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict):
        raise InvalidInputError("video_faceswap skill manifest is invalid")
    return manifest


def run_skill(
    inputs: dict[str, Any],
    options: dict[str, Any] | None = None,
    *,
    comfy_url: str = "http://127.0.0.1:8188",
    timeout_seconds: float = 3600,
) -> dict[str, Any]:
    options = options or {}
    manifest = _load_manifest()

    video = inputs.get("video")
    face = inputs.get("face")
    if not video or not face:
        raise InvalidInputError("Both 'video' and 'face' inputs are required.")

    quality = options.get("quality", "standard")
    profiles = manifest.get("profiles", {})
    if quality not in profiles:
        raise InvalidInputError(
            f"Unsupported quality profile: {quality}",
            details={"allowed": sorted(profiles)},
        )

    workflow_path = SKILL_DIR / profiles[quality]["workflow"]
    raw_bindings = manifest.get("bindings", {})
    bindings = {
        name: Binding(node=str(spec["node"]), field=str(spec["field"]))
        for name, spec in raw_bindings.items()
    }

    client = ComfyClient(comfy_url)
    result = run_workflow(
        client=client,
        workflow_path=workflow_path,
        bindings=bindings,
        file_inputs={"video": video, "face": face},
        timeout_seconds=timeout_seconds,
    )

    output_files = collect_output_files(result.history)
    video_outputs = [
        item
        for item in output_files
        if str(item.get("filename", "")).lower().endswith(
            (".mp4", ".webm", ".mov", ".mkv")
        )
    ]
    if not video_outputs:
        raise OutputNotFoundError(
            "Workflow completed but no video artifact was found in ComfyUI history.",
            details={"prompt_id": result.prompt_id, "outputs": output_files},
        )

    return {
        "job_id": result.prompt_id,
        "status": "completed",
        "outputs": {"video": video_outputs[0]},
        "metadata": {
            "skill": f"{manifest['name']}@{manifest['version']}",
            "profile": quality,
            "backend": comfy_url,
            "uploaded_inputs": result.uploaded_inputs,
        },
    }
