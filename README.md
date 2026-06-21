# 公众号 LLM Wiki

面向公众号阅读与收藏的个人知识库，专为 Cursor + LLM 优化。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 收藏一篇文章
python scripts/collect.py "https://mp.weixin.qq.com/s/xxxxx" --tags ai

# 3. 搜索
python scripts/search.py "agent"
python scripts/search.py --tag ai --status archived
```

## 在 Cursor 中使用

本项目内置两个 Skill：

### 知识库管理（`wechat-wiki`）

- **「收藏这篇文章」** + 粘贴链接或正文
- **「帮我总结 inbox 里的文章」**
- **「归档这篇文章」**
- **「我收藏过哪些关于 Agent 的文章？」**

### 阅读价值评估（`article-evaluator`）

在读之前先评估，避免浪费时间：

- **「评价这篇文章值不值得读」** + 链接或正文
- **「帮我打分」**

首次只返回**简报**（分数 + 读的价值 + Wiki 新/已有对比）。追问才展开细节——速查表见 **[article-evaluator/README.md](.cursor/skills/article-evaluator/README.md)**：

| 追问 | 得到 |
|------|------|
| 展开评分 | 五维分数、红旗、文章画像 |
| 给摘要 | 内容摘要、该读哪几节 |
| **梳理名词** | 陌生术语口语解释，对照 wiki 标新/已有 |
| **展开 wiki 对比** | 与 wiki 的详细新/重复对照 |
| 能学到什么 | 能/不能学到的 |
| 推荐文章 | **联网**找更优替代（评估时不联网） |
| 完整报告 | 汇总并可选存档 |

## 目录说明

```
├── wiki/                  # 知识库主体（Markdown）
│   ├── inbox/             # 收件箱：快速收藏，待整理
│   ├── articles/          # 已归档文章（按年/月）
│   ├── sources/           # 关注的公众号
│   └── notes/             # 跨文章综合笔记
├── templates/             # 文章、公众号、日报模板
├── scripts/
│   ├── collect.py         # 采集公众号文章
│   ├── archive.py         # 归档 inbox 文章（幂等）
│   └── search.py          # 搜索知识库
└── .cursor/skills/
    ├── wechat-wiki/       # 知识库管理
    └── article-evaluator/ # 阅读价值评估

docs/
└── daily-recommend/       # 每日公众号推荐方案（待确认）
```

## 脚本说明

| 脚本 | 干什么 | 什么时候会跑 |
|------|--------|--------------|
| `scripts/collect.py --fetch-only` | 抓公众号正文，**不落盘** | 你说「打分 / 评估」时 |
| `scripts/collect.py` | 抓取并保存到 `wiki/inbox/` | 你说「收藏这篇文章」时 |
| `scripts/collect.py --archive` | 抓取并保存到 `wiki/articles/`（**slug 幂等**） | 你说「归档」且要直接入库时 |
| `scripts/archive.py` | inbox → articles/（**slug 幂等**） | 你说「归档这篇文章」时 |
| `scripts/search.py` | 搜索 wiki 里的文章 | 你说「搜知识库」或追问「推荐文章」时 |

**评估不会自动收藏或归档。** 之前评估时误用了 `collect.py`（无 `--fetch-only`），会把文章写进 inbox——已改为评估只读。

## 工作流

```
阅读公众号 → （可选）先评估打分 → 决定收藏 → inbox → 整理笔记 → 说「归档」→ articles
```

### 推荐习惯

1. **先收藏后整理**：看到好文章先 `collect.py`，别等「有空再看」
2. **让 AI 写 summary**：一句话摘要决定日后能不能搜到
3. **笔记写行动项**：「我的笔记」里至少留一个可执行的行动项
4. **定期写综述**：每月在 `wiki/notes/` 写一篇主题综述

## 采集失败怎么办

微信有反爬机制，链接抓取可能失败。备选方案：

```bash
# 手动粘贴正文
python scripts/collect.py \
  --text "粘贴的文章正文" \
  --title "文章标题" \
  --source "公众号名称" \
  --tags ai,product
```

或在 Cursor 中直接粘贴正文，说「按 wiki 模板收藏到 inbox」。

## 文章 Frontmatter 字段

| 字段 | 说明 |
|------|------|
| `title` | 文章标题 |
| `source` | 公众号名称 |
| `url` | 原文链接 |
| `tags` | 标签列表，如 `[ai, agent]` |
| `status` | `inbox` / `archived` / `reading` |
| `summary` | 一句话摘要（检索关键） |

## License

Personal use.
