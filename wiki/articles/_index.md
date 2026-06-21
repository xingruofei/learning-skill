# 文章库

已归档的公众号文章，按 `年/月` 组织。

## 2026

### 06 月

- [AI Agent & Skill 测评方案及落地实践](2026/06/20260621-ai-agent-skill-测评方案及落地实践.md) — 81 分 · Agent/Skill 测评框架 + TPerf 落地
- [AI测试卷到下半场，最被低估的工程难题浮出水面](2026/06/20260621-ai测试卷到下半场-最被低估的工程难题浮出水面.md) — 56 分 · AI 测试信号治理
- [Harness不是目的，知识才是护城河](2026/06/20260618-harness不是目的-知识才是护城河-一个ai工程交付团队的知识沉淀实践.md) — 68 分 · 腾讯 AI Team 知识分层与 Harness 实践

## 归档规范

路径格式：`articles/YYYY/MM/YYYYMMDD-slug.md`

文件名规则：
- 日期前缀：`YYYYMMDD`
- slug：标题 slug，保留中文，小写连字符
- 示例：`20260618-harness不是目的-知识才是护城河.md`

**幂等**：归档时按 slug（及 url）去重，`python scripts/archive.py` 或 `collect.py --archive` 遇到已存在则跳过，不重复写入。
