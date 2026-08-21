# Architecture

## 1. Core abstraction

The framework is intentionally split into four layers:

```text
Agent      = Goal
Skill      = Capability
Workflow   = Implementation
ComfyUI    = Execution Engine
```

This separation is the central architectural rule of the project.

### Agent

The agent understands user intent, chooses a capability, fills parameters, chains capabilities, and decides whether a retry or fallback is appropriate.

Examples:

- Hermes
- OpenClaw
- Claude-based agents
- Codex-based agents
- Custom orchestrators

The agent should **not** need to know ComfyUI node IDs, custom-node internals, sampler topology, or model installation paths.

### Skill

A skill is a stable agent-facing capability contract.

Examples:

- `video_faceswap`
- `video_upscale`
- `image_to_video`
- `lipsync`
- `face_restore`

A skill may have multiple workflow implementations.

### Workflow

A workflow is a versioned ComfyUI API-format JSON graph that implements a capability.

Example mapping:

```text
video_faceswap
├── fast     → faceswap_fast_v1.json
├── standard → faceswap_standard_v3.json
└── high     → faceswap_quality_v2.json
```

### ComfyUI

ComfyUI is the deterministic GPU execution engine. Production agents submit validated workflows through the gateway rather than interacting with the ComfyUI browser UI.

---

## 2. High-level architecture

```text
                           Agent Layer

                Hermes               OpenClaw
                   │                    │
                   └─────────┬──────────┘
                             ▼
                       Skill Registry
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
             Face Swap    Upscale    Lip Sync
                  │          │          │
                  └──────────┼──────────┘
                             ▼
                       Comfy Gateway
                             │
                  ┌──────────┼───────────┐
                  ▼          ▼           ▼
             Local GPU   Remote GPU   Cloud GPU
                  │          │           │
                  └──────────┼───────────┘
                             ▼
                           ComfyUI
                             │
                             ▼
                       Output Artifact
```

---

## 3. Why agents should not operate the ComfyUI UI

Avoid this production path:

```text
Agent
  ↓
Browser automation
  ↓
Click ComfyUI nodes
  ↓
Upload files
  ↓
Queue Prompt
```

It is fragile because UI layout, node positions, browser state, focus, and timing become part of the execution contract.

Prefer:

```text
Agent
  ↓
Skill call
  ↓
Gateway
  ↓
Workflow Registry
  ↓
Patch approved inputs only
  ↓
ComfyUI API
```

The UI remains useful for developers to design and validate workflows, but it is not part of normal runtime execution.

---

## 4. Gateway responsibilities

The Comfy Gateway isolates agent runtimes from ComfyUI internals.

Responsibilities:

1. Accept stable skill requests.
2. Validate files and parameters.
3. Resolve skill + profile to a workflow version.
4. Patch only declared workflow inputs.
5. Submit workflows to a ComfyUI backend.
6. Track queue and execution state.
7. Stream or expose progress.
8. Collect output artifacts.
9. Normalize errors.
10. Retry or fall back according to policy.
11. Record workflow version, backend, timing, and output metadata.

Suggested public API:

```http
POST   /v1/jobs
GET    /v1/jobs/{job_id}
POST   /v1/jobs/{job_id}/cancel
GET    /v1/jobs/{job_id}/outputs
GET    /v1/capabilities
```

Example request:

```json
{
  "skill": "video_faceswap",
  "inputs": {
    "video": "input://video.mp4",
    "face": "input://face.jpg"
  },
  "options": {
    "quality": "standard"
  }
}
```

---

## 5. Workflow Registry

The registry is a first-class component, not a convenience file.

It answers:

- Which workflows implement a skill?
- Which workflow version is currently active?
- Which inputs are patchable?
- Which output nodes contain artifacts?
- What models/custom nodes are required?
- How much VRAM is expected?
- Which backends can run the workflow?
- What fallback workflow should be used?

Example:

```yaml
video_faceswap:
  version: "1.0"
  profiles:
    fast:
      workflow: skills/video_faceswap/workflows/fast.json
      estimated_vram_gb: 8
    standard:
      workflow: skills/video_faceswap/workflows/standard.json
      estimated_vram_gb: 12
    high:
      workflow: skills/video_faceswap/workflows/quality.json
      estimated_vram_gb: 16

  inputs:
    video:
      node: "12"
      field: video
    face:
      node: "25"
      field: image

  outputs:
    video:
      node: "94"
```

Production workflows should be immutable once released. Changes create a new workflow version.

---

## 6. Job state machine

Recommended state model:

```text
CREATED
   ↓
VALIDATING
   ↓
QUEUED
   ↓
RUNNING
   ↓
POST_PROCESSING
   ↓
QA
   ↓
COMPLETED
```

Failure/recovery path:

```text
RUNNING
   ├── RETRYING ──→ QUEUED
   ├── CANCELLED
   └── FAILED
```

Minimum job record:

```text
id
skill
skill_version
workflow_version
backend
status
progress
inputs
outputs
comfy_prompt_id
attempt
created_at
started_at
finished_at
error_code
error_message
```

---

## 7. Backend abstraction

Skills should not care where inference runs.

```text
GenerationBackend
├── LocalComfyBackend
├── RemoteComfyBackend
└── CloudBackend
```

Possible routing policy:

```text
Face swap        → RTX workstation
Whisper/audio    → Mac mini
Heavy video      → Cloud GPU
Upscale          → RTX workstation
```

This allows the framework to become a GPU skill server for multiple agents.

---

## 8. Agent chaining

A major benefit appears when agents combine deterministic skills.

Example request:

> Replace the face in this video, restore the face, and upscale the final video to 1080p.

Possible plan:

```text
video_faceswap
      ↓
face_restore
      ↓
video_upscale
      ↓
media_quality_check
```

Another example:

```text
image
  ↓
image_to_video
  ↓
TTS
  ↓
lipsync
  ↓
video_upscale
  ↓
MP4
```

The agent owns planning; each skill remains narrow and testable.

---

## 9. Meta skill

A future high-level skill can expose natural media routing:

```text
comfy_media
```

Example conceptual call:

```text
comfy_media.generate(
    task="replace face and upscale",
    inputs=...
)
```

Internally it can route to primitive skills. Primitive skills remain available for deterministic tool calls and testing.

---

## 10. Production restrictions

Agents should be allowed to:

- discover capabilities
- choose an approved workflow profile
- provide declared inputs
- set bounded parameters
- submit jobs
- inspect status
- retry/cancel according to policy
- retrieve artifacts

Agents should not have unrestricted permission to:

- rewrite arbitrary workflow graphs
- delete nodes
- install arbitrary custom nodes
- download arbitrary models
- mutate production workflow files
- change backend security configuration

This keeps the execution environment reproducible and reduces agent-induced drift.

---

## 11. Safety, consent, and provenance

Identity-changing workflows such as face swap require additional safeguards in production.

Recommended controls:

- explicit user attestation that they have permission to use the supplied identity/media
- configurable retention period for uploaded media
- automatic deletion of temporary files
- job-level audit metadata
- provenance/watermark metadata where appropriate
- configurable deny/approval policies for sensitive deployment contexts

These controls should live in the gateway/policy layer rather than inside individual ComfyUI graphs.
