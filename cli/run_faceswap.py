from __future__ import annotations

import argparse
import json

from gateway.errors import GatewayError
from skills.video_faceswap.handler import run_skill


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ComfyUI video face-swap skill headlessly.")
    parser.add_argument("--video", required=True, help="Path to source video")
    parser.add_argument("--face", required=True, help="Path to reference face image")
    parser.add_argument("--quality", choices=["fast", "standard", "high"], default="standard")
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=float, default=3600)
    args = parser.parse_args()

    try:
        result = run_skill(
            {"video": args.video, "face": args.face},
            {"quality": args.quality},
            comfy_url=args.comfy_url,
            timeout_seconds=args.timeout,
        )
    except GatewayError as exc:
        print(json.dumps({"status": "failed", "error": exc.to_dict()}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
