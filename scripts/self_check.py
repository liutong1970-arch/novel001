#!/usr/bin/env python3
"""Tiny smoke check for the local naturalness pipeline."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from naturalness_pipeline import scan_rows, write_scan_table, write_segment_queue, write_wenxin_v6_report


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "正文"
        report = root / "自然度报告"
        source.mkdir()
        report.mkdir()
        (source / "第1章.md").write_text(
            "他决定推开门。\n门外电话响了。\n她看到血迹。\n这一切都变了。\n",
            encoding="utf-8",
        )

        rows = scan_rows(source)
        assert len(rows) == 1
        assert rows[0][1].name == "第1章.md"

        scan_table = report / "自然度本地风险表.md"
        v6_report = report / "wenxin-v6-综合质检报告.md"
        segment_queue = report / "自然度分段修订队列.md"
        write_scan_table(rows, scan_table)
        write_wenxin_v6_report(rows, v6_report)
        write_segment_queue(source, segment_queue, threshold=0)

        assert "第1章.md" in scan_table.read_text(encoding="utf-8")
        assert "综合质检报告" in v6_report.read_text(encoding="utf-8")
        assert "第1章.md" in segment_queue.read_text(encoding="utf-8")


if __name__ == "__main__":
    main()
