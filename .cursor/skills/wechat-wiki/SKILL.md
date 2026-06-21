---
name: wechat-wiki
description: >-
  Manage a personal LLM wiki for WeChat public account articles: collect, archive,
  search, summarize, and answer questions across saved articles. Use when the
  user mentions 公众号, 收藏文章, 知识库, wiki, 归档, 阅读笔记, or wants to save/search/summarize
  WeChat articles in this project.
---

# 公众号 LLM Wiki

个人知识库，专为公众号阅读与收藏设计。所有文章以 Markdown + YAML frontmatter 存储，便于 LLM 检索和推理。

## 目录结构

```
wiki/
├── _index.md          # 总索引
├── _tags.md           # 标签索引
├── inbox/             # 待整理（快速收藏）
├── articles/YYYY/MM/  # 已归档
├── sources/           # 公众号源
└── notes/             # 跨文章综合笔记
```

## 核心工作流

### 1. 收藏文章

**有链接时**，运行采集脚本：

```bash
pip install -r requirements.txt
python scripts/collect.py "<公众号链接>" --tags ai,product
```

**抓取失败时**（微信反爬），请用户粘贴正文，用手动模式：

```bash
python scripts/collect.py --text "正文" --title "标题" --source "公众号名" --tags ai
```

**在对话中收藏**：用户发链接或正文，按 `templates/article.md` 格式写入 `wiki/inbox/`。

### 2. 阅读与批注

打开 inbox 中的文章，帮用户：
- 提炼「核心观点」3-5 条写入 frontmatter 的 `summary` 和正文区块
- 补充「我的笔记」：启发、疑问、行动项
- 建议合适标签

### 3. 归档

**优先用脚本（按文件名 slug 幂等，重复文章不会反复归档）：**

```bash
python scripts/archive.py wiki/inbox/文章文件名.md
python scripts/archive.py --inbox 20260618-foo.md
```

脚本会：
- 将文章移至 `wiki/articles/YYYY/MM/`
- 更新 frontmatter `status: archived`
- 若 `articles/` 中已有**同 slug**（或同 url）的归档 → 跳过移动，并清理 inbox 副本

手动归档时同样遵循幂等：先 `find_existing_archive` 检查 slug，已存在则不再移动、不重复更新索引。

归档后还需：
- 在 `wiki/articles/_index.md` 添加链接
- 在 `wiki/_tags.md` 对应标签下添加链接
- 若为新公众号，在 `wiki/sources/` 创建源文件
- 更新 `wiki/_index.md` 统计

### 4. 搜索与问答

搜索命令：

```bash
python scripts/search.py "关键词"
python scripts/search.py --tag ai
python scripts/search.py --status inbox
```

回答知识库问题时：
1. 先 `scripts/search.py` 或 grep `wiki/` 找相关文章
2. 读取 frontmatter 的 `summary` 快速筛选
3. 深入阅读匹配文章的「核心观点」和「我的笔记」
4. 综合多篇文章给出答案，注明来源路径

### 5. 写综合笔记

用户要求「写一篇关于 XX 的综述」时：
- 搜索相关文章
- 在 `wiki/notes/` 创建 `主题名.md`
- 结构：背景 → 各文章观点对比 → 个人结论 → 推荐阅读顺序

### 6. 归档对话 / 问答整理

**非公众号内容**（Cursor 对话、概念梳理、多文对比）归档到 `wiki/notes/`，不走 `collect.py`。

用户说「归档到知识库」「保存这次问答」「整理进 wiki」时：

1. 按 [templates/note.md](../../templates/note.md) 写入 `wiki/notes/YYYYMMDD-主题slug.md`
2. frontmatter 必填：`title`、`type: note`、`source: cursor-chat`、`summary`、`tags`
3. 若有依据的文章，填 `related:` 链接到 `wiki/articles/`
4. 更新 `wiki/notes/_index.md`、`wiki/_index.md`、`_tags.md`

**与公众号文章的区别**：

| | 公众号文章 | 阅读笔记 |
|---|-----------|----------|
| 目录 | `inbox/` → `articles/` | `notes/` |
| 采集 | `collect.py <url>` | 对话中直接写文件 |
| frontmatter | `source` = 公众号名 | `type: note`，`source: cursor-chat` |
| 搜索 | ✅ | ✅（`search.py` 已包含 notes） |

## 文章格式要求

每篇文章必须包含 YAML frontmatter：

```yaml
title: ""
source: ""        # 公众号名
author: ""
url: ""
published: ""     # YYYY-MM-DD
collected: ""
tags: []
status: inbox     # inbox | archived | reading
summary: ""       # 一句话，LLM 检索关键字段
```

## 常用对话指令

| 用户说 | 你做 |
|--------|------|
| 收藏这篇文章 | 采集或手动创建 → inbox |
| 值不值得读 / 评价这篇文章 | 使用 `article-evaluator` skill 打分评估 |
| 帮我读/总结这篇 | 读文章，填核心观点 + 摘要 |
| 归档 | 移至 articles/，更新索引 |
| 我收藏过哪些关于 XX 的 | search + 综合回答 |
| 关注 XX 公众号 | 在 sources/ 创建源文件 |
| 写阅读日报 | 用 templates/daily-digest.md |
| 保存这次评估 | 写入 `wiki/evaluations/` |
| **归档到知识库 / 保存问答** | 写入 `wiki/notes/`（见「归档对话」） |

## 注意事项

- `summary` 字段是 LLM 检索的核心，归档前务必填写
- 图片链接来自微信 CDN，可能过期，重要图片建议本地保存到 `assets/`
- 不要删除用户的「我的笔记」内容
- 索引文件（`_index.md`、`_tags.md`）保持简洁，只列链接和一句话描述

## 详细参考

- 文章模板：[templates/article.md](../../templates/article.md)
- 笔记模板：[templates/note.md](../../templates/note.md)
- 公众号模板：[templates/source.md](../../templates/source.md)
