# Video Face Swap Skill

## Purpose

Replace a face in an existing video using a user-supplied reference face image.

This skill is an agent-facing capability. The caller does not need to know ComfyUI node IDs, workflow topology, sampler settings, custom-node configuration, or model paths.

## Use this skill when

The user wants to:

- replace a person's face in an existing video
- apply a reference face identity to a video subject
- generate a face-swapped version of a supplied source video

Do not use this skill when the user only wants general image editing, face restoration, video upscaling, or image-to-video generation.

## Required inputs

1. `video` — source video file
2. `face` — reference face image

## Optional inputs

- `quality`
  - `fast`
  - `standard` (default)
  - `high`

## Output

- `video` — processed MP4 artifact

## Agent behavior

1. Ensure both required files are present.
2. Ensure the requested use is authorized under the deployment policy.
3. Do not ask the user for ComfyUI implementation details.
4. Submit the job through the Comfy Gateway.
5. Track the returned job ID.
6. Report meaningful progress if the runtime supports it.
7. Retry only through approved gateway retry/fallback policies.
8. Return the final video artifact after successful completion.

## Tool-style contract

Conceptual call:

```text
comfy_video_faceswap(
    video=<file>,
    face=<image>,
    quality="standard"
)
```

Conceptual success response:

```json
{
  "status": "completed",
  "job_id": "job_123",
  "outputs": {
    "video": "artifact://job_123/result.mp4"
  },
  "metadata": {
    "skill": "video_faceswap@0.1.0",
    "workflow": "faceswap_standard@0.1.0",
    "backend": "rtx-pc-01"
  }
}
```

## Error handling

The agent should reason over normalized error codes rather than raw ComfyUI stack traces.

Examples:

```text
INVALID_INPUT
FACE_NOT_DETECTED
GPU_OOM
BACKEND_UNAVAILABLE
EXECUTION_FAILED
OUTPUT_NOT_FOUND
POLICY_DENIED
```

Examples of allowed recovery:

```text
GPU_OOM
→ gateway may retry with a lower-memory profile

FACE_NOT_DETECTED
→ gateway may retry with an approved alternate detector workflow

BACKEND_UNAVAILABLE
→ gateway may route to another approved backend
```

The agent should not dynamically rewrite the production ComfyUI graph as an ad-hoc recovery strategy.

## Production restrictions

This skill must not grant unrestricted ability to:

- edit arbitrary workflow nodes
- install custom nodes
- download arbitrary models
- modify backend configuration
- mutate production workflow versions

Only fields declared in the workflow registry may be patched at runtime.

## First POC acceptance criteria

- Hermes or OpenClaw discovers this skill.
- A source video and face image can be passed to it.
- The skill launches ComfyUI execution through the gateway.
- No manual ComfyUI browser interaction is required.
- Job status/progress can be retrieved.
- A successful run returns `result.mp4`.
- Job metadata records the skill, workflow, and backend versions.
