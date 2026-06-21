#!/usr/bin/env python3
"""Create a local revision queue for high-risk fiction segments (wenxin-v6)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from naturalness_batch_scan import iter_files
from naturalness_scan import cn_len, scan_text


def split_segments(text: str, window_chars: int = 900, overlap_chars: int = 160) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    segments: list[tuple[int, int, str]] = []
    start_line = 1
    current: list[str] = []
    current_chars = 0

    for idx, line in enumerate(lines, 1):
        line_chars = cn_len(line)
        current.append(line)
        current_chars += line_chars
        if current_chars >= window_chars:
            body = "\n".join(current).strip()
            if body:
                segments.append((start_line, idx, body))
            tail: list[str] = []
            tail_chars = 0
            for old_line in reversed(current):
                tail.insert(0, old_line)
                tail_chars += cn_len(old_line)
                if tail_chars >= overlap_chars:
                    break
            current = tail
            start_line = max(1, idx - len(tail) + 1)
            current_chars = tail_chars

    body = "\n".join(current).strip()
    if body:
        segments.append((start_line, len(lines), body))
    return segments


def action_for(result: dict) -> str:
    parts = []
    # L0: segment-level warning threshold is 45, intentionally more sensitive than chapter-level rhythm_risk >55.
    if result["rhythm_risk"] >= 45:
        parts.append("打散段长和句长，加入一处长段或短促中断")
    if result["pattern_risk"] >= 45:
        parts.append("清理模板壳、高概率词链和同构句式")
    if result["texture_risk"] >= 45:
        parts.append("补角色误判、身体反应、具体物件或现场取舍")
    if result["stats_risk"] >= 45:
        parts.append("减少设定说明密度，改成行动中的信息释放")
    # wenxin-v6 新增
    if result.get("level3_hits"):
        parts.append(f"三级禁词违规：{'; '.join(f'{k}:{v}' for k,v in result['level3_hits'].items())}")
    if result.get("like_count", 0) > 3:
        parts.append(f'"像"句式过多（{result["like_count"]}次，限额3次）')
    return "；".join(parts) or "轻修：保留剧情，只调节局部呼吸和手迹"


def preview(text: str, limit: int = 90) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    return one_line[:limit] + ("..." if len(one_line) > limit else "")


def segment_rows(path: Path, threshold: float = 38.0) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows = []
    for index, (start, end, body) in enumerate(split_segments(text), 1):
        result = scan_text(body, f"{path.name}:{index}")
        if result["total_risk"] >= threshold:
            rows.append(
                {
                    "file": path.name,
                    "start_line": start,
                    "end_line": end,
                    "total": result["total_risk"],
                    "rhythm": result["rhythm_risk"],
                    "pattern": result["pattern_risk"],
                    "texture": result["texture_risk"],
                    "stats": result["stats_risk"],
                    "chars": result["chars_cn"],
                    "action": action_for(result),
                    "preview": preview(body),
                }
            )
    rows.sort(key=lambda row: row["total"], reverse=True)
    return rows


def queue_text(rows: list[dict]) -> str:
    lines = ["# 自然度分段修订队列（wenxin-v6）", ""]
    if not rows:
        lines.append("暂无超过阈值的片段。")
    else:
        lines.extend(
            [
                "| 总分 | 节奏 | 语言 | 纹理 | 统计 | 字数 | 位置 | 修订动作 | 片段预览 |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
            ]
        )
        for row in sorted(rows, key=lambda row: row["total"], reverse=True):
            location = f"{row['file']}:{row['start_line']}-{row['end_line']}"
            lines.append(
                f"| {row['total']:.1f} | {row['rhythm']:.1f} | {row['pattern']:.1f} | "
                f"{row['texture']:.1f} | {row['stats']:.1f} | {row['chars']} | {location} | "
                f"{row['action']} | {row['preview']} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a segment-level naturalness revision queue (wenxin-v6).")
    parser.add_argument("target", type=Path, help="A draft file or a directory containing draft files.")
    parser.add_argument("--threshold", type=float, default=38.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    files = iter_files(args.target.expanduser())
    rows = []
    for path in files:
        rows.extend(segment_rows(path, threshold=args.threshold))

    output = queue_text(rows)
    if args.output:
        args.output.expanduser().parent.mkdir(parents=True, exist_ok=True)
        args.output.expanduser().write_text(output, encoding="utf-8")
        print(args.output.expanduser())
    else:
        print(output)


if __name__ == "__main__":
    main()
