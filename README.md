# ComfyUI Skill Framework

Turn ComfyUI workflows into reusable AI-agent capabilities for Hermes, OpenClaw, and other agent runtimes.

## Vision

ComfyUI should be treated as a **GPU execution engine**, not as the end-user interface.

The framework separates four concerns:

- **Agent = Goal** — understands what the user wants.
- **Skill = Capability** — exposes a stable tool contract to the agent.
- **Workflow = Implementation** — contains deterministic ComfyUI graphs and model choices.
- **ComfyUI = Execution Engine** — runs the GPU workflow and returns artifacts.

```text
User
  ↓
Hermes / OpenClaw / Other Agent
  ↓
Skill Router
  ↓
ComfyUI Skill
  ↓
Comfy Gateway
  ↓
Workflow Registry
  ↓
ComfyUI
  ↓
GPU / Cloud
  ↓
Result Artifact
```

## Why this exists

A normal ComfyUI workflow may expose dozens or hundreds of nodes. An agent should not need to understand or mutate all of them.

Instead, the agent should see a small, stable interface such as:

```text
video_faceswap(
    video,
    face,
    quality="standard"
)
```

The skill maps that call to a versioned workflow such as:

```text
quality=fast     → faceswap_fast_v1.json
quality=standard → faceswap_standard_v1.json
quality=high     → faceswap_quality_v1.json
```

The workflow implementation can evolve without changing the agent-facing contract.

## Design principles

1. **Capability-first abstraction** — one skill represents a user capability, not necessarily one workflow file.
2. **Locked workflows in production** — agents select workflows and parameters but do not freely rewrite production graphs.
3. **Workflow versioning** — every production workflow is versioned and reproducible.
4. **Gateway isolation** — Hermes/OpenClaw should not depend directly on ComfyUI internals.
5. **Deterministic execution** — agent planning and GPU execution are separated.
6. **Portable backends** — local ComfyUI, remote GPU nodes, or cloud workers can sit behind the same skill contract.
7. **Observable jobs** — every task has explicit status, progress, errors, retries, and output metadata.

## Initial target capability

The first proof of concept will be a video face-swap skill:

```text
Input:
- source video
- reference face image
- quality profile

Output:
- processed MP4
```

Target acceptance criteria:

1. Hermes or OpenClaw can discover the skill.
2. The agent can provide `video + face` inputs.
3. The skill submits a job to ComfyUI without manual UI interaction.
4. Progress and errors can be observed.
5. The final `result.mp4` is returned to the caller.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — Agent / Skill / Workflow / ComfyUI layering, gateway, registry, job model, backend routing, chaining, and production restrictions.
- [Skill Specification](docs/SKILL_SPEC.md) — skill package contract, manifests, normalized errors, retry policy, versioning, and POC acceptance criteria.
- [Roadmap](docs/ROADMAP.md) — phased implementation plan from hardened workflow to Hermes/OpenClaw integration and multi-backend GPU routing.
- [Capability Registry Example](config/capabilities.example.yaml) — example backend/capability/workflow registry.
- [Video Face Swap Skill Example](examples/video_faceswap/SKILL.md) — first agent-facing skill template.

## Planned repository structure

```text
comfy-agent-skills/
├── README.md
├── gateway/
│   ├── api/
│   ├── comfy_client/
│   ├── jobs/
│   └── registry/
├── skills/
│   ├── video_faceswap/
│   │   ├── SKILL.md
│   │   ├── skill.yaml
│   │   ├── handler.py
│   │   └── workflows/
│   │       ├── fast.json
│   │       ├── standard.json
│   │       └── quality.json
│   ├── video_upscale/
│   ├── image_to_video/
│   ├── lipsync/
│   └── video_to_video/
├── common/
│   ├── storage.py
│   ├── job.py
│   └── media.py
├── config/
│   ├── capabilities.yaml
│   └── comfy.yaml
└── tests/
```

## Future capabilities

- Video face swap
- Image face swap
- Face restore
- Video upscale
- Lip sync
- Image-to-video
- Video-to-video
- Media QA
- Automatic retry and fallback routing
- Multi-GPU / local + cloud routing

## Safety and provenance

Face-swap and identity-changing workflows should be used only with appropriate authorization. Production deployments should include consent/authorization checks, retention controls for uploaded media, audit metadata, and provenance/watermarking where appropriate.

## Status

Architecture definition and MVP planning in progress.
