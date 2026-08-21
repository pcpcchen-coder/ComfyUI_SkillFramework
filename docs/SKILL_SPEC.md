# Skill Specification

## 1. Skill model

A skill represents a reusable user-facing capability. It is intentionally more stable than any individual ComfyUI workflow.

Recommended package layout:

```text
skills/video_faceswap/
├── SKILL.md
├── skill.yaml
├── handler.py
└── workflows/
    ├── fast.json
    ├── standard.json
    └── quality.json
```

A skill can expose one capability while internally choosing among several workflow implementations.

---

## 2. Example manifest

```yaml
name: comfy_video_faceswap
version: "0.1.0"
description: Replace a person's face in an existing video using a reference face image.

inputs:
  video:
    type: file
    media_type: video
    required: true

  face:
    type: file
    media_type: image
    required: true

options:
  quality:
    type: enum
    values: [fast, standard, high]
    default: standard

outputs:
  video:
    type: file
    media_type: video/mp4

policies:
  requires_identity_authorization: true
  temporary_input_retention: true
```

---

## 3. Agent-facing usage guidance

`SKILL.md` should tell Hermes/OpenClaw when and how to invoke the capability without exposing ComfyUI details.

Example:

```markdown
# Video Face Swap

Use this skill when the user wants to replace a face in an existing video using a reference face image.

Required inputs:

1. Source video
2. Reference face image

Optional input:

- quality: fast | standard | high

Do not ask the user for ComfyUI node IDs, sampler settings, model paths, or custom-node parameters.

Execution policy:

1. Validate both media files.
2. Confirm the user has authorization to use the supplied identity/media when required by policy.
3. Submit the job through the Comfy Gateway.
4. Monitor status.
5. Retry only through approved fallback policies.
6. Return the final video artifact.
```

---

## 4. Handler contract

The skill handler translates the agent-facing request into a gateway job.

Conceptual Python interface:

```python
class SkillResult:
    job_id: str
    status: str
    outputs: dict
    metadata: dict


def run_skill(inputs: dict, options: dict) -> SkillResult:
    ...
```

The handler should not contain full ComfyUI graph logic. Workflow resolution belongs to the registry/gateway.

---

## 5. Quality profiles

Skills should expose simple semantic controls rather than low-level inference parameters.

Example:

```text
fast
standard
high
```

The implementation can map them to different workflows or bounded parameter profiles:

```text
fast
→ lower resolution / faster workflow

standard
→ default production workflow

high
→ quality-first workflow / additional restoration / larger processing resolution
```

The mapping is implementation-specific and versioned.

---

## 6. Capability discovery

The framework should expose machine-readable capability discovery.

Example:

```yaml
skills:
  video_faceswap:
    enabled: true
    backends: [rtx-pc-01]
    estimated_vram_gb: 12

  video_upscale:
    enabled: true
    backends: [rtx-pc-01]

  image_to_video:
    enabled: true
    backends: [cloud-video-01]

  lipsync:
    enabled: true
    backends: [rtx-pc-01]
```

Agents can then reason about available capabilities without knowing model installation details.

---

## 7. Primitive skills vs meta skill

Recommended two-level model:

### Primitive skills

Deterministic and narrow:

```text
comfy_video_faceswap
comfy_video_upscale
comfy_image_to_video
comfy_lipsync
comfy_face_restore
```

### Meta skill

High-level routing/orchestration:

```text
comfy_media
```

The meta skill can plan/chains primitive skills, but primitive skills remain individually callable and testable.

---

## 8. Error contract

Errors should be normalized before returning to the agent.

Suggested codes:

```text
INVALID_INPUT
UNSUPPORTED_MEDIA
FACE_NOT_DETECTED
WORKFLOW_VALIDATION_FAILED
BACKEND_UNAVAILABLE
GPU_OOM
EXECUTION_FAILED
OUTPUT_NOT_FOUND
CANCELLED
POLICY_DENIED
```

An error payload should contain:

```json
{
  "code": "GPU_OOM",
  "retryable": true,
  "message": "The selected backend did not have enough VRAM.",
  "suggested_action": "retry_with_lower_memory_profile"
}
```

Avoid exposing raw stack traces to normal users; preserve them in internal logs.

---

## 9. Retry and fallback rules

Retries must be policy-driven rather than improvised by the agent.

Example:

```yaml
retry_policy:
  max_attempts: 2

  rules:
    GPU_OOM:
      action: switch_profile
      target: fast

    FACE_NOT_DETECTED:
      action: switch_workflow
      target: alternate_detector

    BACKEND_UNAVAILABLE:
      action: switch_backend
```

This keeps behavior reproducible.

---

## 10. Versioning rules

Version independently:

- skill contract version
- workflow version
- model/custom-node dependency set
- gateway API version

A completed job should record all of these so outputs can be reproduced later.

Recommended identifiers:

```text
skill: video_faceswap@0.1.0
workflow: faceswap_standard@1.3.0
backend: rtx-pc-01
```

---

## 11. First POC acceptance criteria

For `comfy_video_faceswap`:

1. Hermes or OpenClaw can discover the skill.
2. The caller can supply one source video and one face image.
3. No manual ComfyUI UI interaction is required.
4. The gateway chooses the approved workflow.
5. Only declared workflow inputs are patched.
6. The job exposes status and progress.
7. Common failures are normalized into stable error codes.
8. The resulting MP4 is returned as an artifact.
9. Job metadata records skill/workflow/backend versions.
10. Temporary inputs are cleaned according to configured retention policy.
