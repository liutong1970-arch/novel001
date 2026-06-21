#!/usr/bin/env python3
"""Batch naturalness scan for Chinese fiction drafts (wenxin-v6)."""

from __future__ import annotations

import argparse
from pathlib import Path

from naturalness_scan import scan


SUPPORTED_SUFFIXES = {".txt", ".md"}
SKIP_PREFIXES = ("README",)


def iter_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(
        p
        for p in target.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_SUFFIXES
        and not p.name.startswith(SKIP_PREFIXES)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch scan fiction drafts for naturalness risks (wenxin-v6).")
    parser.add_argument("target", type=Path, help="A draft file or a directory containing draft files.")
    parser.add_argument("--threshold", type=float, default=35.0, help="Show chapters at or above this score first.")
    args = parser.parse_args()

    files = iter_files(args.target.expanduser())
    if not files:
        raise SystemExit(f"No draft files found: {args.target}")

    rows = []
    for path in files:
        result = scan(path)
        rows.append(
            (
                result["total_risk"],
                result["rhythm_risk"],
                result["pattern_risk"],
                result["texture_risk"],
                result["stats_risk"],
                result["chars_cn"],
                result.get("like_count", 0),
                result.get("level3_hits", {}),
                len(result.get("repetitions", [])),
                len(result.get("pov_drifts", [])),
                result.get("hook_strength", {}).get("strength", "?"),
                path,
            )
        )

    rows.sort(key=lambda row: row[0], reverse=True)
    print("总分  节奏  语言  纹理  统计  字数  像  三级禁词  重复  POV  钩子  文件")
    for total, rhythm, pattern, texture, stats, chars, like_count, level3, reps, pov, hook, path in rows:
        mark = "!" if total >= args.threshold else " "
        l3_str = ";".join(f"{k}:{v}" for k, v in level3.items()) if level3 else "-"
        print(
            f"{mark}{total:5.1f} {rhythm:5.1f} {pattern:5.1f} "
            f"{texture:5.1f} {stats:5.1f} {chars:5d} {like_count:2d} {l3_str:<8s} "
            f"{reps:2d} {pov:2d} {hook:<2s}  {path.name}"
        )


if __name__ == "__main__":
    main()
