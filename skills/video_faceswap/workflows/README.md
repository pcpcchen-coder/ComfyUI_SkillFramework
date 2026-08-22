# FaceSwap workflow integration

This directory intentionally does **not** ship a fabricated FaceSwap graph.

The framework is ready for a real ComfyUI API-format workflow, but the exact node graph depends on the FaceSwap/custom-node stack installed on the target ComfyUI instance.

## Required files

Export the tested workflow from ComfyUI in API format and place one or more profiles here:

```text
fast.json
standard.json
high.json
```

You may initially use the same known-good workflow for all three profiles and split them later.

## Bindings

After exporting the workflow, update `../skill.yaml` so these semantic inputs point at the real API-format node ids and input fields:

```yaml
bindings:
  video:
    node: "<video loader node id>"
    field: "<video input field>"
  face:
    node: "<reference image loader node id>"
    field: "<image input field>"
```

The gateway will reject attempts to patch any undeclared node input.

## P0 validation

Before wiring Hermes/OpenClaw, validate the workflow manually in ComfyUI at least several times with representative media. Then export that exact graph in API format.

## P1 validation

With ComfyUI running on `127.0.0.1:8188`:

```bash
python -m cli.run_faceswap \
  --video /path/source.mp4 \
  --face /path/face.jpg \
  --quality standard
```

Expected result: the command uploads both inputs, queues the locked workflow through `/prompt`, polls `/history/{prompt_id}`, and prints a normalized result containing the video artifact descriptor.
