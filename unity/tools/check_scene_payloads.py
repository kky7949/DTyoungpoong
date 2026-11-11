"""Read-only publication check for generated mesh data embedded in Unity scenes."""

import argparse
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenes", type=Path,
        default=Path(__file__).resolve().parents[1] / "Assets" / "Scenes",
        help="Scene directory to inspect without modifying it",
    )
    scenes = parser.parse_args().scenes
    files = sorted(scenes.glob("*.unity"))
    if not files:
        parser.error("No .unity scenes found")

    failed = []
    for scene in files:
        data = scene.read_bytes()
        if re.search(rb"(?m)^--- !u!43 |(?:m_IndexBuffer|m_VertexData|_typelessdata):", data):
            failed.append(scene.name)
    if failed:
        print("FAIL: embedded mesh payloads: " + ", ".join(failed))
        print("Keep company geometry external; review an export copy before publishing.")
        return 1

    print(f"PASS: {len(files)} scenes contain no serialized mesh payloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
