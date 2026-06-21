#!/usr/bin/env python3
"""
采集微信公众号文章，保存为 LLM Wiki 格式的 Markdown 文件。

用法:
    python scripts/collect.py <url> [--archive] [--tags tag1,tag2]
    python scripts/collect.py <url> --fetch-only          # 仅抓取，不写入 wiki
    python scripts/collect.py --text "粘贴的正文" --title "标题" --source "公众号名"

示例:
    python scripts/collect.py "https://mp.weixin.qq.com/s/xxxxx"
    python scripts/collect.py "https://mp.weixin.qq.com/s/xxxxx" --archive --tags ai,agent
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from wiki_util import (
    ROOT,
    WIKI,
    archive_dest_dir,
    find_existing_archive,
    make_filename,
    make_slug,
    resolve_archive_date,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_wechat_article(url: str) -> dict:
    """从微信公众号链接抓取文章元数据和正文。"""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "lxml")

    title_el = soup.select_one("#activity-name") or soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else "未命名文章"

    source_el = soup.select_one("#js_name") or soup.select_one(".profile_nickname")
    source = source_el.get_text(strip=True) if source_el else ""

    author_el = soup.select_one("#js_author_name") or soup.select_one(".rich_media_meta_text")
    author = author_el.get_text(strip=True) if author_el else ""

    time_el = soup.select_one("#publish_time") or soup.select_one("#meta_content .rich_media_meta_text")
    published = ""
    if time_el:
        time_text = time_el.get_text(strip=True)
        match = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", time_text)
        if match:
            published = re.sub(r"[年月/]", "-", match.group(1)).strip("-")
            published = re.sub(r"-+", "-", published)

    content_el = soup.select_one("#js_content") or soup.select_one(".rich_media_content")
    if not content_el:
        raise ValueError("无法提取文章正文，页面结构可能已变化或需要登录")

    for tag in content_el.find_all(["script", "style"]):
        tag.decompose()

    body_md = html_to_markdown(content_el)

    return {
        "title": title,
        "source": source,
        "author": author,
        "url": url,
        "published": published,
        "body": body_md,
    }


def html_to_markdown(element) -> str:
    """将 HTML 元素粗略转为 Markdown。"""
    lines: list[str] = []

    for child in element.descendants:
        if child.name in ("h1", "h2", "h3", "h4"):
            level = int(child.name[1])
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")
        elif child.name == "p":
            text = child.get_text(strip=True)
            if text:
                lines.append(f"{text}\n")
        elif child.name == "li":
            text = child.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif child.name == "strong" or child.name == "b":
            if child.parent and child.parent.name not in ("p", "li", "h1", "h2", "h3", "h4"):
                text = child.get_text(strip=True)
                if text:
                    lines.append(f"**{text}**")
        elif child.name == "img":
            alt = child.get("alt", "图片")
            src = child.get("data-src") or child.get("src", "")
            if src:
                lines.append(f"\n![{alt}]({src})\n")

    if not lines:
        return element.get_text("\n", strip=True)

    return "\n".join(lines)


def build_frontmatter(data: dict, tags: list[str], status: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    fm = {
        "title": data["title"],
        "source": data.get("source", ""),
        "author": data.get("author", ""),
        "url": data.get("url", ""),
        "published": data.get("published", ""),
        "collected": today,
        "tags": tags,
        "status": status,
        "summary": "",
    }
    return yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)


def build_markdown(data: dict, tags: list[str], status: str) -> str:
    fm = build_frontmatter(data, tags, status)
    tag_str = ", ".join(f"`{t}`" for t in tags) if tags else "—"
    url = data.get("url", "")

    return f"""---
{fm.strip()}
---

# {data["title"]}

## 元信息

| 字段 | 值 |
|------|-----|
| 公众号 | {data.get("source", "—")} |
| 作者 | {data.get("author", "—")} |
| 发布日期 | {data.get("published", "—")} |
| 原文链接 | [打开]({url}) |
| 标签 | {tag_str} |

## 核心观点

> 阅读后补充 3-5 条要点

1.
2.
3.

## 正文

{data.get("body", "")}

## 我的笔记

### 启发

### 疑问

### 行动项

- [ ]

## 关联

- 相关文章：
- 相关笔记：
"""


def save_article(content: str, data: dict, archive: bool) -> tuple[Path, bool]:
    """保存文章。返回 (路径, 是否新建)；已归档则跳过写入。"""
    title = data["title"]
    url = data.get("url", "")

    existing = find_existing_archive(title=title, url=url)
    if existing:
        return existing, False

    when = resolve_archive_date(data)
    filename = make_filename(title, when)
    dest_dir = archive_dest_dir(when) if archive else WIKI / "inbox"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    if not archive and dest.exists():
        slug = make_slug(title)
        date_prefix = when.strftime("%Y%m%d")
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{date_prefix}-{slug}-{counter}.md"
            counter += 1

    dest.write_text(content, encoding="utf-8")
    return dest, True


def validate_wechat_url(url: str) -> bool:
    parsed = urlparse(url)
    return "mp.weixin.qq.com" in parsed.netloc


def main():
    parser = argparse.ArgumentParser(description="采集微信公众号文章到 LLM Wiki")
    parser.add_argument("url", nargs="?", help="微信公众号文章链接")
    parser.add_argument("--archive", action="store_true", help="直接归档到 articles/ 而非 inbox/")
    parser.add_argument("--tags", default="", help="标签，逗号分隔，如 ai,agent")
    parser.add_argument("--text", help="手动粘贴的正文（跳过网页抓取）")
    parser.add_argument("--title", default="", help="手动模式下的标题")
    parser.add_argument("--source", default="", help="手动模式下的公众号名")
    parser.add_argument("--author", default="", help="手动模式下的作者")
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="仅抓取并输出正文，不写入 wiki（评估文章时使用）",
    )
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    status = "archived" if args.archive else "inbox"

    if args.text:
        data = {
            "title": args.title or "未命名文章",
            "source": args.source,
            "author": args.author,
            "url": args.url or "",
            "published": "",
            "body": args.text,
        }
    elif args.url:
        if not validate_wechat_url(args.url):
            print(f"警告: 链接不是微信公众号域名: {args.url}", file=sys.stderr)
        print(f"正在抓取: {args.url}")
        try:
            data = fetch_wechat_article(args.url)
        except Exception as e:
            print(f"抓取失败: {e}", file=sys.stderr)
            print("\n备选方案: 复制文章正文，使用 --text 参数手动导入", file=sys.stderr)
            print(
                f'  python scripts/collect.py --text "正文内容" --title "标题" --source "公众号名"',
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"标题: {data['title']}")
        print(f"公众号: {data.get('source', '—')}")
    else:
        parser.print_help()
        sys.exit(1)

    if args.fetch_only:
        print(f"标题: {data['title']}", file=sys.stderr)
        print(f"公众号: {data.get('source', '—')}", file=sys.stderr)
        print(f"作者: {data.get('author', '—')}", file=sys.stderr)
        print(data.get("body", ""))
        sys.exit(0)

    content = build_markdown(data, tags, status)
    dest, created = save_article(content, data, args.archive)

    if not created:
        print(f"\n已归档，跳过: {dest.relative_to(ROOT)}")
        print("  同 slug/url 已存在于 articles/，未重复写入")
        sys.exit(0)

    print(f"\n已保存: {dest.relative_to(ROOT)}")
    print(f"状态: {'已归档' if args.archive else '收件箱（待整理）'}")
    print("\n下一步:")
    print("  1. 在 Cursor 中打开该文件，补充「核心观点」和「我的笔记」")
    if not args.archive:
        print("  2. 运行 python scripts/archive.py <inbox路径> 归档（幂等）")
    print("  3. 更新 wiki/_tags.md 和 wiki/sources/ 索引")


if __name__ == "__main__":
    main()
