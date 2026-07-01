---
name: tech-news-aggregator
description: Set up automated daily tech news aggregation from GitHub Trending, Hugging Face Daily Papers, Hacker News, arXiv, Hackaday, Ollama, Edge Impulse, and Anthropic.
category: devops
trigger: |
  - User says "帮我每天搜集/整理/汇总 信息/新闻/前沿"
  - User asks about tech news, AI papers, GitHub trending, industry monitoring
  - User says "搭一个自动化脚本每天搜寻信息"
  - User asks for morning briefing or daily digest
---

# Tech News Aggregator

Hermes Agent cron job skill — daily scrapes 9 tech sources, summarizes in Chinese, delivers to QQ/Feishu/WeChat.

## Sources

| # | Source | Endpoint | Proxy | Reliability |
|---|--------|----------|-------|-------------|
| 1 | **GitHub Trending** | `GET /search/repositories?q=created:>YYYY-MM-DD&sort=stars` | ✅ | ⭐⭐⭐⭐⭐ JSON API |
| 2 | **HF Daily Papers** | `GET huggingface.co/api/daily_papers` | ✅ | ⭐⭐⭐⭐⭐ JSON API |
| 3 | **Hacker News** | Firebase REST: `/v0/topstories.json` + `/v0/item/{id}.json` | ❌直连更快 | ⭐⭐⭐⭐⭐ |
| 4 | **arXiv** | `export.arxiv.org/api/query?search_query=cat:cs.{AI,RO,LG,CL}` | ✅ | ⭐⭐⭐ Atom XML |
| 5 | **Hackaday** | `hackaday.com/blog/` HTML scrape `<h2 class="entry-title">` | ✅ | ⭐⭐⭐⭐ |
| 6 | **Key Repos** | `GET /repos/{owner}/{repo}` (11 verified repos) | ✅ | ⭐⭐⭐⭐ |
| 7 | **Ollama** | `ollama.com/library` → `x-test-model-title` attr or `/api/tags` JSON | ✅ | ⭐⭐⭐⭐ |
| 8 | **Edge Impulse** | `edgeimpulse.com/blog/category/all/rss/` Atom XML | ✅ | ⭐⭐⭐ |
| 9 | **Anthropic** | `anthropic.com/news` → `<h4>` headline extraction | ✅ | ⭐⭐ (partial) |

**Failed/skip:** Reddit (blocked), IEEE Spectrum (JS-rendered), LangChain Blog (SSL-blocked).

## Cron Job Setup

```
cronjob(action='create',
  schedule='0 8 * * *',
  deliver='qqbot:YOUR_CHANNEL_ID',  # or feishu:oc_xxx
  model={'model':'deepseek-chat','provider':'deepseek'},
  enabled_toolsets=['terminal','web']
)
```

Key prompt template (self-contained, copy into `prompt` field):

```
⚠️ 代理: 检查代理是否运行，没运行就启动（参照你的代理工具文档）
⚠️ 所有curl加 --proxy $PROXY_URL --max-time 15
⚠️ 每个源只试1次，失败标[DATA FAILED]跳过
⚠️ 完毕后停止代理

Collect from: GitHub Trending / HF Papers / HN / arXiv(AI+RO+LG+CL) /
Hackaday / Key Repos / Ollama / Edge Impulse / Anthropic

Output format: 每条标题 + ```代码块``` 技术说明（架构/方法/原理）
Section headers: 【🔥GitHub】【📄HF Papers】【💡HN】【📄arXiv】【🔧Hackaday】【📊Key Repos】【📦Others】【📊Summary】
```

## Output Format (Panoramic Mode)

```
━━━ 每日简报 YYYY-MM-DD ━━━

【🔥 GitHub 今日热门】
1. owner/repo — ⭐XXk · language
```技术说明
解决什么问题、技术架构、关键创新、方向标签
```

【📄 HF 每日论文】
Paper Title
```研究问题、方法/架构、核心创新、方向标签
```

【💡 Hacker News】
· Title (▲score)
```内容概要、为什么上首页
```

【📄 arXiv】
cs.AI: Paper Title
```解决的问题、技术方法要点
```

【📊 关键仓库动态】
repo (⭐XXk) → 技术方向描述

【📊 今日总结】
400-600字：信息最密集方向+证据 / 趋势提炼 / 其他亮点 / 技术分析
```

## User Interest Directions (5+2)

| Direction | Keywords |
|-----------|----------|
| **Edge AI / TinyML** | quantization, TFLite, edge inference, FPGA, INT8 |
| **AI Agent** | agent, multi-agent, MCP, tool-use, function calling |
| **机器人** | robot, embodied, VLA, ROS, humanoid, sim2real |
| **小模型** | SLM, Phi, Qwen-mini, distillation, MoE |
| **边缘硬件** | ESP32, RK3588, RISC-V, FPGA, MCU, NPU |
| + Industrial IoT | OPC UA, TSN, SCADA, predictive maintenance |
| + 能源行业 | 电力系统, 光伏, VPP, 储能BMS |

## Key Pitfalls (Top 8)

1. **每个curl必须加 `--max-time 15`** — 否则一个源卡死拖垮整个cron
2. **GitHub API直连不走代理** — 代理IP被限速，直连IP干净
3. **HN不走代理** — Firebase是Google端点，直连15s，代理60s+
4. **arXiv每分类单独query** — 合并查询结果不全
5. **先存文件再解析** — `curl -o /tmp/x.json && python3 parse.py`，不要pipe到python3（WSL安全策略拦截）
6. **QQ单行≤40字** — 手机端截断，详细内容放```代码块```
7. **send_message读启动时config** — mid-session改config不生效，用cron deliver参数
8. **DeepSeek流式180s超时** — 纯脚本方案见 `scripts/daily_briefing.py`

## Standalone Script

`scripts/daily_briefing.py` — 无LLM依赖的独立Python脚本，9个源模块化收集。

```bash
export PROXY_URL="http://your-proxy:port"
export PROXY_BIN="your-proxy-binary"
export FEISHU_APP_ID="xxx"
export FEISHU_APP_SECRET="xxx"
export FEISHU_HOME_CHANNEL="oc_xxx"
python3 scripts/daily_briefing.py
```

## Verification

Before going live: `cronjob(action='run', job_id=...)` — verify all 9 sources return data.
