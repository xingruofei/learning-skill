# 每日公众号推荐 · 方案草案

> **状态：待确认 · 2026-06-18 讨论记录**  
> 尚未实现，具体细节后续再定。

## 背景

希望每天（定时或手动）获取「关注的优质公众号昨天发了什么」，经评估后推荐值得读的文章，并与现有 wiki + article-evaluator 打通。

## 核心约束

**微信没有「搜全网昨天好文章」的公开 API。** 可行路径：

```
你维护优质公众号清单 → 定时拉更新 → 过滤/去重/评估 → 出推荐简报
```

## 架构

```
wiki/sources/watchlist.yaml   关注清单 + 兴趣标签
        ↓
拉取层（RSS / 脚本）          昨天新文候选池
        ↓
过滤                          主题、去重、已读
        ↓
article-evaluator             简报：分数 + Wiki 新/已有
        ↓
wiki/daily/YYYY-MM-DD.md      每日推荐输出
```

## 三层设计

### 1. 源层

- 扩展 `wiki/sources/*.md`：rss_url、topics、quality_tier
- 新增 `wiki/sources/watchlist.yaml`：汇总关注号 + 兴趣过滤

### 2. 拉取层

| 方案 | 说明 | 状态 |
|------|------|------|
| **A. WeWe RSS（推荐）** | Docker 部署，微信读书订阅公众号，输出 JSON/RSS | 待确认是否部署 |
| **B. WeRSS** | 类似，带 Web 管理界面 | 备选 |
| **C. 纯手动 MVP** | 「今日推荐」+ WebSearch，零部署 | 可先落地 |

参考：[WeWe RSS](https://github.com/cooderl/wewe-rss)

### 3. 推荐层

- 去重：`wiki/seen/urls.txt` + 已归档 articles
- 主题过滤：ai / testing / agent / 研发
- 评估：article-evaluator 简报（≥60 分或 Top 3–5）
- 输出：`wiki/daily/YYYY-MM-DD.md`

## 触发方式

| 方式 | 说明 | 状态 |
|------|------|------|
| 手动 | Cursor 说「今日推荐」 | 待实现 skill |
| cron | `0 8 * * * python scripts/daily_recommend.py` | 待 Phase 2 |
| Cursor Automation | IDE 定时 Agent | 待 Phase 3 |

## 分阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | watchlist + daily-digest skill + 手动触发 | 未开始 |
| **Phase 2** | WeWe RSS + fetch_rss.py + daily_recommend.py | 未开始 |
| **Phase 3** | 自动评估 + cron 定时 | 未开始 |

## 计划目录结构（实现时）

```
scripts/
  daily_recommend.py      # 主流程
  fetch_rss.py            # 读 RSS/JSON
wiki/
  sources/watchlist.yaml
  daily/                  # 每日推荐
  seen/urls.txt           # 已处理 URL
.agents/skills/
  daily-digest/           # 「今日推荐」skill
```

## 待确认事项

- [ ] 是否本地部署 WeWe RSS？用哪个微信读书账号？
- [ ] 初始 watchlist 放哪些公众号？（AI / 测试 / 研发）
- [ ] 先做 Phase 1 手动，还是直接 Phase 2？
- [ ] 日报推送到哪？（仅 wiki 文件 / Cursor 通知 / 其他）
- [ ] 推荐阈值：≥60 分还是 Top N？
- [ ] 定时几点跑？（建议早上 8:00）

## 与现有系统关系

| 已有 | 用途 |
|------|------|
| article-evaluator | 评分 + Wiki 对比 |
| wiki/sources/ | 公众号清单 |
| wiki/articles/ | 去重（已归档不推） |
| collect.py --fetch-only | 评估时不落盘 |

## 讨论记录

- 2026-06-18：首次提出需求，确定「curated 清单 + RSS + 评估简报」方向；用户要求先建目录记录，细节后续讨论。
