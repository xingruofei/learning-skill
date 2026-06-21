"""Shared helpers for wiki article paths and idempotent archive checks."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from slugify import slugify

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
ARTICLES = WIKI / "articles"

FILENAME_RE = re.compile(r"^(\d{8})-(.+?)(?:-\d+)?$")


def make_slug(title: str, max_len: int = 40) -> str:
    slug = slugify(title, max_length=max_len, word_boundary=True, allow_unicode=True)
    return slug or "article"


def extract_slug_from_filename(name: str) -> Optional[str]:
    stem = Path(name).stem
    match = FILENAME_RE.match(stem)
    return match.group(2) if match else None


def extract_date_prefix_from_filename(name: str) -> Optional[str]:
    stem = Path(name).stem
    match = FILENAME_RE.match(stem)
    return match.group(1) if match else None


def make_filename(title: str, when: Optional[datetime] = None) -> str:
    when = when or datetime.now()
    return f"{when.strftime('%Y%m%d')}-{make_slug(title)}.md"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, match.group(2)


def update_frontmatter_status(text: str, status: str) -> str:
    fm, body = parse_frontmatter(text)
    fm["status"] = status
    dumped = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{dumped.strip()}\n---\n{body}"


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def resolve_archive_date(fm: dict, source_name: str = "") -> datetime:
    for key in ("published", "collected"):
        parsed = _parse_date(str(fm.get(key) or ""))
        if parsed:
            return parsed
    prefix = extract_date_prefix_from_filename(source_name)
    if prefix:
        parsed = _parse_date(prefix)
        if parsed:
            return parsed
    return datetime.now()


def archive_dest_dir(when: datetime) -> Path:
    return ARTICLES / when.strftime("%Y") / when.strftime("%m")


def iter_archived_paths() -> list[Path]:
    if not ARTICLES.exists():
        return []
    return [
        path
        for path in ARTICLES.rglob("*.md")
        if not path.name.startswith("_")
    ]


def find_archived_by_slug(slug: str) -> Optional[Path]:
    if not slug:
        return None
    for path in iter_archived_paths():
        existing = extract_slug_from_filename(path.name)
        if existing == slug:
            return path
    return None


def find_archived_by_url(url: str) -> Optional[Path]:
    url = (url or "").strip()
    if not url:
        return None
    for path in iter_archived_paths():
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if (fm.get("url") or "").strip() == url:
            return path
    return None


def find_existing_archive(title: str = "", url: str = "") -> Optional[Path]:
    slug = make_slug(title) if title else ""
    if slug:
        hit = find_archived_by_slug(slug)
        if hit:
            return hit
    if url:
        return find_archived_by_url(url)
    return None
