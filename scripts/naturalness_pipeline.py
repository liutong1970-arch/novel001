#!/usr/bin/env python3
"""Run the local naturalness workflow for a fiction project (wenxin-v6)."""

from __future__ import annotations

import argparse
from pathlib import Path

from naturalness_batch_scan import iter_files
from naturalness_segment_queue import queue_text, segment_rows
from naturalness_scan import scan


def scan_rows(source_dir: Path) -> list[tuple[dict, Path]]:
    rows = [(scan(path), path) for path in iter_files(source_dir)]
    rows.sort(key=lambda row: row[0]["total_risk"], reverse=True)
    return rows


def print_scan_rows(rows: list[tuple[dict, Path]], threshold: float) -> None:
    print("总分  节奏  语言  纹理  统计  字数  像  三级禁词  重复  POV  钩子  文件")
    for result, path in rows:
        mark = "!" if result["total_risk"] >= threshold else " "
        level3 = result.get("level3_hits", {})
        l3_str = ";".join(f"{k}:{v}" for k, v in level3.items()) if level3 else "-"
        print(
            f"{mark}{result['total_risk']:5.1f} {result['rhythm_risk']:5.1f} "
            f"{result['pattern_risk']:5.1f} {result['texture_risk']:5.1f} "
            f"{result['stats_risk']:5.1f} {result['chars_cn']:5d} {result.get('like_count', 0):2d} "
            f"{l3_str:<8s} {len(result.get('repetitions', [])):2d} "
            f"{len(result.get('pov_drifts', [])):2d} {result.get('hook_strength', {}).get('strength', '?'):<2s}  "
            f"{path.name}"
        )


def write_scan_table(rows: list[tuple[dict, Path]], output: Path) -> None:
    lines = [
        "# 自然度本地风险表",
        "",
        "| 总分 | 节奏 | 语言 | 纹理 | 统计 | 字数 | 文件 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result, path in rows:
        lines.append(
            f"| {result['total_risk']:.1f} | {result['rhythm_risk']:.1f} | "
            f"{result['pattern_risk']:.1f} | {result['texture_risk']:.1f} | "
            f"{result['stats_risk']:.1f} | {result['chars_cn']} | {path.name} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def low_quality_level(result: dict) -> str:
    """Map scan output to the v6 quality-governance risk level.

    L0 thresholds:
    - P0: total_risk > 70 with E < 4, or multiple hard failures.
    - P1: total_risk > 55, or watered content with E < 6.
    - P2: 35 < total_risk <= 55, or repetition/POV/weak-hook issues.
    - P3: banned-pattern or light template risk.
    """
    hard_failures = sum(
        [
            bool(result["info_density"]["is_watered"]),
            bool(result["hook_strength"]["is_weak"]),
            bool(result["pov_drifts"]),
            bool(result["repetitions"]),
            result["engagement_score"] < 4,
        ]
    )
    if (result["total_risk"] > 70 and result["engagement_score"] < 4) or hard_failures >= 3:
        return "P0"
    if result["total_risk"] > 55 or (result["info_density"]["is_watered"] and result["engagement_score"] < 6):
        return "P1"
    if (35 < result["total_risk"] <= 55) or result["repetitions"] or result["pov_drifts"] or result["hook_strength"]["is_weak"]:
        return "P2"
    if result["pattern_hits"] or result["level3_hits"]:
        return "P3"
    return "通过"


def write_wenxin_v6_report(rows: list[tuple[dict, Path]], output: Path) -> None:
    """wenxin-v6 综合质检报告（自然度、追读力、重复段落、POV、低质风险）。"""
    lines = [
        "# wenxin-v6 综合质检报告",
        "",
        "## 重复段落检测",
        "",
    ]

    rep_issues = 0
    for r, path in rows:
        fname = path.name
        if r["repetitions"]:
            lines.append(f"### {fname}")
            for rep in r["repetitions"]:
                lines.append(f"- 段落 {rep['para_i']+1} ↔ {rep['para_j']+1}，相似度 {rep['similarity']:.0%}")
                lines.append(f"  - `{rep['text_i']}`")
                lines.append(f"  - `{rep['text_j']}`")
                rep_issues += 1
            lines.append("")

    if rep_issues == 0:
        lines.append("无重复段落问题。")
        lines.append("")

    lines.extend([
        "## POV 一致性",
        "",
    ])

    pov_issues = 0
    for r, path in rows:
        fname = path.name
        if r["pov_drifts"]:
            lines.append(f"### {fname}")
            for pd in r["pov_drifts"]:
                lines.append(f"- 段落 {pd['paragraph_index']+1}: {pd['text']}")
                pov_issues += 1
            lines.append("")

    if pov_issues == 0:
        lines.append("无 POV 漂移问题。")
        lines.append("")

    lines.extend([
        "## 章末钩子强度",
        "",
        "| 文件 | 钩子强度 | 最后一段 |",
        "| --- | --- | --- |",
    ])

    weak_hooks = 0
    for r, path in rows:
        fname = path.name
        hook = r["hook_strength"]
        mark = "⚠️" if hook["is_weak"] else "✅"
        lines.append(f"| {fname} | {mark} {hook['strength']} | {hook['last_paragraph'][:40]} |")
        if hook["is_weak"]:
            weak_hooks += 1

    lines.extend(["", "## 信息密度", ""])
    lines.extend([
        "| 文件 | 密度/500字 | 状态 |",
        "| --- | --- | --- |",
    ])

    watered = 0
    for r, path in rows:
        fname = path.name
        info = r["info_density"]
        status = "⚠️ 注水" if info["is_watered"] else "✅"
        lines.append(f"| {fname} | {info['density_per_500']} | {status} |")
        if info["is_watered"]:
            watered += 1

    lines.extend(["", "## 追读力与低质风险", ""])
    lines.extend([
        "| 文件 | 追读力E | 自然度风险 | 低质风险 | 优先动作 |",
        "| --- | --- | --- | --- | --- |",
    ])

    quality_risks = 0
    for r, path in rows:
        fname = path.name
        level = low_quality_level(r)
        if level != "通过":
            quality_risks += 1
        if level in ("P0", "P1", "P2") and r["engagement_score"] < 6:
            action = "先修结构和追读"
        elif level in ("P0", "P1", "P2"):
            action = "先重写问题段"
        elif r["engagement_score"] < 6:
            action = "补信息增量/爽点/钩子"
        else:
            action = "常规润色"
        lines.append(
            f"| {fname} | {r['engagement_score']:.1f} | {r['total_risk']:.1f} | {level} | {action} |"
        )

    lines.extend(["", f"## 汇总", ""])
    lines.append(f"- 重复段落问题：{rep_issues} 处")
    lines.append(f"- POV 漂移问题：{pov_issues} 处")
    lines.append(f"- 弱钩子章节：{weak_hooks} 章")
    lines.append(f"- 注水章节：{watered} 章")
    lines.append(f"- 低质风险章节：{quality_risks} 章")
    lines.append("")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_segment_queue(source_dir: Path, output: Path, threshold: float) -> None:
    rows = []
    for path in iter_files(source_dir):
        rows.extend(segment_rows(path, threshold=threshold))
    output.write_text(queue_text(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local naturalness scan and segment queue (wenxin-v6).")
    parser.add_argument("--project-dir", type=Path, default=Path.home() / "Desktop" / "都市商铺")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--chapter-threshold", type=float, default=35.0)
    parser.add_argument("--segment-threshold", type=float, default=38.0)
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser()
    source_dir = (args.source_dir or project_dir / "正文").expanduser()
    report_dir = (args.report_dir or project_dir / "自然度报告").expanduser()
    report_dir.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        raise SystemExit(f"正文目录不存在：{source_dir}")

    print("1. 批量扫描章节自然度")
    rows = scan_rows(source_dir)
    if not rows:
        raise SystemExit(f"No draft files found: {source_dir}")
    print_scan_rows(rows, args.chapter_threshold)

    print("2. 写入章节风险表")
    scan_table = report_dir / "自然度本地风险表.md"
    write_scan_table(rows, scan_table)
    print(scan_table)

    print("3. 生成 wenxin-v6 综合质检报告（重复段落/POV/钩子/信息密度）")
    v6_report = report_dir / "wenxin-v6-综合质检报告.md"
    write_wenxin_v6_report(rows, v6_report)
    print(v6_report)

    print("4. 生成分段修订队列")
    segment_queue = report_dir / "自然度分段修订队列.md"
    write_segment_queue(source_dir, segment_queue, args.segment_threshold)
    print(segment_queue)

    print("完成。下一步只修改高分片段，保留剧情、事实和角色声音。")


if __name__ == "__main__":
    main()
