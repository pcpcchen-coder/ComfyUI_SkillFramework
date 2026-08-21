# Roadmap

## Goal

Build a reusable framework that turns validated ComfyUI workflows into stable agent skills for Hermes, OpenClaw, and other runtimes.

The implementation should prove one end-to-end capability first, then generalize.

---

## Phase 0 — Workflow hardening

Target: establish a reliable manual ComfyUI workflow for the first capability.

First capability:

```text
video + reference face → face-swapped MP4
```

Tasks:

- choose the face-swap workflow stack
- define required models/custom nodes
- validate input formats
- test multiple source videos and face images
- establish fast / standard / high profiles if useful
- export API-format workflow JSON
- record expected VRAM and runtime constraints

Acceptance criteria:

- workflow succeeds repeatedly in ComfyUI
- workflow output is deterministic enough for automation
- required input node IDs/fields are documented
- output artifact node is known
- dependencies are reproducible

Recommended test target: at least 20 representative runs before treating the workflow as production-ready.

---

## Phase 1 — Headless ComfyUI execution

Target: run the same workflow without opening the ComfyUI UI.

Tasks:

- implement ComfyUI API client
- implement file upload/input mapping
- implement workflow patching for approved fields only
- submit jobs to ComfyUI
- capture `prompt_id`
- monitor execution/progress
- collect result artifacts
- normalize execution errors

Minimal acceptance flow:

```text
video.mp4
+
face.jpg
+
workflow_api.json
        ↓
CLI / Python
        ↓
result.mp4
```

Acceptance criteria:

- no browser automation
- no manual Queue button
- API produces valid MP4
- failure is observable
- output path/artifact is returned programmatically

---

## Phase 2 — Gateway

Target: hide ComfyUI-specific details behind a stable API.

Tasks:

- implement `/v1/jobs`
- implement job persistence
- implement workflow registry
- implement capability registry
- implement backend abstraction
- implement job status/progress
- implement cancellation
- implement output retrieval
- implement temporary-file retention policy

Acceptance criteria:

- caller never sends raw ComfyUI workflow JSON
- caller refers to a skill/capability name
- gateway resolves the correct workflow
- each completed job records workflow/backend versions

---

## Phase 3 — Hermes / OpenClaw skill integration

Target: make the capability directly callable by an agent runtime.

First skill:

```text
comfy_video_faceswap
```

Tasks:

- create `SKILL.md`
- create machine-readable manifest
- implement gateway tool wrapper
- add capability discovery
- define user-facing error handling
- define authorization/consent gate for identity-changing workflows

Acceptance criteria:

1. Hermes/OpenClaw discovers the skill.
2. User provides video + face image.
3. Agent invokes the skill.
4. Skill creates a gateway job.
5. Progress/error can be inspected.
6. Final MP4 is returned to the user.

---

## Phase 4 — Additional primitive skills

Add capabilities one at a time using the same pattern:

```text
comfy_video_upscale
comfy_face_restore
comfy_lipsync
comfy_image_to_video
comfy_video_to_video
```

Each skill must have:

- stable input/output contract
- approved workflow(s)
- versioned dependencies
- acceptance tests
- bounded options
- error mapping
- backend requirements

---

## Phase 5 — Agent chaining

Target: allow an orchestrator to combine primitive skills.

Example:

```text
video_faceswap
      ↓
face_restore
      ↓
video_upscale
      ↓
media_quality_check
```

Tasks:

- artifact passing between skills
- chain-level job tracking
- per-step retry/fallback
- intermediate file cleanup
- final artifact selection

Acceptance criteria:

- each primitive skill stays independently callable
- chain execution can be resumed/diagnosed by step
- one failed step does not erase prior diagnostic information

---

## Phase 6 — Meta skill

Target: expose a higher-level capability such as:

```text
comfy_media
```

It can translate a broad request into a plan of primitive skills while preserving deterministic execution underneath.

Example request:

> Replace this face, restore the face, and upscale to 1080p.

Possible plan:

```text
comfy_video_faceswap
→ comfy_face_restore
→ comfy_video_upscale
```

---

## Phase 7 — Multi-backend GPU routing

Target: turn the framework into a reusable GPU Skill Server.

Possible backend topology:

```text
Mac mini       → audio / lightweight tasks
RTX PC         → face swap / upscale / lip sync
Cloud GPU      → heavy video generation
```

Tasks:

- backend health checks
- capability/backend matrix
- VRAM-aware routing
- queue-aware routing
- cost-aware cloud routing
- failover

---

## Suggested MVP scope

Do not start with multi-agent orchestration.

MVP should contain only:

```text
1 × ComfyUI instance
1 × Comfy Gateway
1 × video_faceswap skill
1 × Hermes or OpenClaw integration
```

The first milestone is successful when the following user journey works end to end:

```text
User sends video + face image
        ↓
Hermes/OpenClaw chooses video_faceswap
        ↓
Skill submits job
        ↓
Gateway resolves locked workflow
        ↓
ComfyUI processes video
        ↓
Gateway collects result
        ↓
Agent returns result.mp4
```

Everything else should build on this pattern.
