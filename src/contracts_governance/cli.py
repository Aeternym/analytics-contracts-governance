from __future__ import annotations

import argparse
import json
from pathlib import Path

from .validator import save_report, validate_directory


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate synthetic analytics contracts")
    parser.add_argument("path", type=Path, nargs="?", default=Path("examples/contracts"))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Treat an existing empty directory as intentional. Missing paths still fail.",
    )
    args = parser.parse_args(argv)
    report = validate_directory(args.path, allow_empty=args.allow_empty)
    if args.output:
        save_report(report, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

