# Hermes Daily Briefing

> 每日自动技术简报系统 — 基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的 Cron Job 技能

自动从 9 个技术信息源收集数据，生成中文技术简报，推送到 QQ / 飞书 / 微信。

## 数据源

| 源 | 方法 | 需要代理 |
|---|---|---|
| GitHub Trending | Search API / HTML | ✅ |
| Hugging Face Daily Papers | JSON API | ✅ |
| Hacker News | Firebase API | ✅ (或直连) |
| arXiv (cs.AI/RO/LG/CL) | Atom XML | ✅ |
| Hackaday | HTML | ✅ |
| 关键仓库监控 (11个) | GitHub API | ✅ |
| Ollama 新模型 | HTML | ✅ |
| Edge Impulse Blog | RSS | ✅ |
| Anthropic News | HTML | ✅ |

## 快速开始

### 1. 安装 Hermes Agent

```bash
# 参考 https://github.com/NousResearch/hermes-agent
pip install hermes-agent
```

### 2. 安装此技能

```bash
# 复制技能到 Hermes 技能目录
cp -r . ~/.hermes/skills/devops/tech-news-aggregator/
```

### 3. 配置代理（用于访问海外源）

此技能需要代理访问海外数据源。通过环境变量配置：

```
默认代理地址: YOUR_PROXY_URL
```

### 4. 创建 Cron Job

在 Hermes CLI 中：

```
/cron create --schedule "0 8 * * *" --prompt "Load tech-news-aggregator skill. 收集所有9个源的数据，生成全景式中文技术简报。"
```

或使用 Python 脚本模式（无 LLM，纯脚本）：

```bash
# 设置环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_HOME_CHANNEL="oc_your_channel_id"

# 直接运行
python3 scripts/daily_briefing.py
```

### 5. 配置推送渠道

在 `~/.hermes/config.yaml` 中设置：

```yaml
# QQ Bot
QQBOT_HOME_CHANNEL: "qqbot:YOUR_CHANNEL_ID"

# 飞书
FEISHU_HOME_CHANNEL: "oc_your_chat_id"

# 微信 (通过 iLink)
WEIXIN_HOME_CHANNEL: "weixin:your_user_id@im.wechat"
```

## 输出格式

支持 4 种输出模式：

- **Mode A: 全景式** — 全部条目不过滤，每条带方向标签
- **Mode B: 定向过滤** — 按用户兴趣方向筛选
- **Mode C: 快速扫描** — 一行一条，标题+星数
- **Mode D: QQ代码块模式** — 每条带```代码块```详解（推荐QQ推送）

## 项目结构

```
├── README.md                 # 本文件
├── SKILL.md                  # Hermes Agent 技能定义（完整配置+prompt模板）
├── scripts/
│   └── daily_briefing.py     # 独立Python脚本（无LLM依赖）
└── references/
    ├── source-endpoints.md   # 各数据源的API端点和解析方法
    ├── qq-codeblock-format.md # QQ代码块格式模板
    ├── cronjob-system-layout.md # Hermes Cron系统文件布局（调试用）
    ├── direct-script-alternative.md # 无LLM脚本方案说明
    └── simple-source-apis.md # 精简版5源API参考
```

## 已知问题

| 问题 | 解决方案 |
|---|---|
| Reddit API 已封锁 | 跳过此源 |
| IEEE Spectrum 是 JS 渲染 | 跳过此源 |
| arXiv 代理可能超时 | 设 `--max-time 15`，失败跳过 |
| GitHub API 代理IP被限速 | GitHub API 不走代理，直连 |
| DeepSeek 流式超时 | 用 `daily_briefing.py` 纯脚本方案 |

## 许可

MIT

## 致谢

[Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research
