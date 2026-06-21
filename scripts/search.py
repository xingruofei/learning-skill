#!/usr/bin/env python3
"""
在 wiki 中搜索文章与笔记（按标题、标签、摘要、正文关键词）。

用法:
    python scripts/search.py "agent"
    python scripts/search.py --tag ai
    python scripts/search.py --source "某公众号"
    python scripts/search.py --status inbox
    python scripts/search.py --type note
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, match.group(2)


def iter_articles() -> list[tuple[Path, dict, str]]:
    results = []
    for pattern in ["inbox/*.md", "articles/**/*.md", "notes/*.md"]:
        for path in WIKI.glob(pattern):
            if path.name.startswith("_"):
                continue
            text = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(text)
            results.append((path, fm, body))
    return results


def search(
    query: str = "",
    tag: str = "",
    source: str = "",
    status: str = "",
    doc_type: str = "",
) -> list[tuple[Path, dict]]:
    results = []
    query_lower = query.lower()

    for path, fm, body in iter_articles():
        if status and fm.get("status", "") != status:
            continue
        if tag and tag not in (fm.get("tags") or []):
            continue
        if source and source not in (fm.get("source") or ""):
            continue
        if doc_type:
            inferred = fm.get("type") or ("note" if "notes" in path.parts else "article")
            if inferred != doc_type:
                continue
        if query:
            searchable = " ".join([
                fm.get("title", ""),
                fm.get("summary", ""),
                fm.get("source", ""),
                " ".join(fm.get("tags") or []),
                body,
            ]).lower()
            if query_lower not in searchable:
                continue
        results.append((path, fm))

    return results


def doc_kind(path: Path, fm: dict) -> str:
    if fm.get("type"):
        return fm["type"]
    return "note" if "notes" in path.parts else "article"


def main():
    parser = argparse.ArgumentParser(description="搜索 LLM Wiki 文章与笔记")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("--tag", default="", help="按标签筛选")
    parser.add_argument("--source", default="", help="按公众号筛选")
    parser.add_argument("--status", default="", choices=["inbox", "archived", "reading"])
    parser.add_argument("--type", dest="doc_type", default="", choices=["article", "note"], help="按类型筛选")
    args = parser.parse_args()

    if not any([args.query, args.tag, args.source, args.status, args.doc_type]):
        parser.print_help()
        sys.exit(1)

    hits = search(args.query, args.tag, args.source, args.status, args.doc_type)

    if not hits:
        print("未找到匹配内容")
        sys.exit(0)

    print(f"找到 {len(hits)} 条:\n")
    for path, fm in hits:
        rel = path.relative_to(ROOT)
        tags = ", ".join(fm.get("tags") or [])
        kind = doc_kind(path, fm)
        source_label = fm.get("source", "—") if kind == "article" else fm.get("source", "—")
        print(f"  [{kind}] {fm.get('title', '未命名')}")
        print(f"    路径: {rel}")
        if kind == "article":
            print(f"    公众号: {source_label} | 标签: {tags or '—'}")
        else:
            print(f"    来源: {source_label} | 标签: {tags or '—'}")
        if fm.get("summary"):
            print(f"    摘要: {fm['summary']}")
        print()


if __name__ == "__main__":
    main()
