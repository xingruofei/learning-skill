#!/usr/bin/env python3
"""
将 inbox 文章归档到 wiki/articles/，按文件名 slug 幂等。

用法:
    python scripts/archive.py wiki/inbox/20260618-foo.md
    python scripts/archive.py --inbox 20260618-foo.md

若 articles/ 中已有同 slug（或同 url）的归档，跳过移动并清理 inbox 副本。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wiki_util import (
    ROOT,
    WIKI,
    archive_dest_dir,
    extract_slug_from_filename,
    find_existing_archive,
    make_filename,
    make_slug,
    parse_frontmatter,
    resolve_archive_date,
    update_frontmatter_status,
)


def archive_file(source: Path, *, dry_run: bool = False) -> int:
    if not source.exists():
        print(f"文件不存在: {source}", file=sys.stderr)
        return 1

    text = source.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(text)
    title = fm.get("title") or source.stem
    url = fm.get("url") or ""
    slug = extract_slug_from_filename(source.name) or make_slug(title)

    existing = find_existing_archive(title=title, url=url)
    if existing:
        rel = existing.relative_to(ROOT)
        print(f"已归档，跳过: {rel}")
        print(f"  幂等键 slug: {slug}")
        if source.resolve() != existing.resolve() and source.exists():
            if dry_run:
                print(f"  [dry-run] 将删除 inbox 副本: {source.relative_to(ROOT)}")
            else:
                source.unlink()
                print(f"  已删除 inbox 副本: {source.relative_to(ROOT)}")
        return 0

    when = resolve_archive_date(fm, source.name)
    dest_dir = archive_dest_dir(when)
    filename = make_filename(title, when)
    dest = dest_dir / filename

    if dest.exists():
        print(f"已归档，跳过: {dest.relative_to(ROOT)}")
        print(f"  目标文件已存在")
        if source.resolve() != dest.resolve() and source.exists() and not dry_run:
            source.unlink()
            print(f"  已删除 inbox 副本: {source.relative_to(ROOT)}")
        return 0

    updated = update_frontmatter_status(text, "archived")

    if dry_run:
        print(f"[dry-run] 将归档: {source.relative_to(ROOT)}")
        print(f"          → {dest.relative_to(ROOT)}")
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(updated, encoding="utf-8")
    if source.resolve() != dest.resolve():
        source.unlink()

    print(f"已归档: {dest.relative_to(ROOT)}")
    print("\n下一步:")
    print("  1. 更新 wiki/articles/_index.md")
    print("  2. 更新 wiki/_tags.md 与 wiki/sources/（如有新标签/公众号）")
    print("  3. 更新 wiki/_index.md 统计")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="归档 inbox 文章到 wiki/articles/（幂等）")
    parser.add_argument("path", nargs="?", help="inbox 文章路径")
    parser.add_argument("--inbox", help="inbox 下的文件名，如 20260618-foo.md")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入")
    args = parser.parse_args()

    if args.inbox:
        source = WIKI / "inbox" / args.inbox
    elif args.path:
        source = Path(args.path)
        if not source.is_absolute():
            source = ROOT / source
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(archive_file(source, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
