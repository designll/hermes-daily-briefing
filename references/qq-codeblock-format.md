# QQ Code-Block Briefing Format

> User-verified format (2026-06-02 session). Delivered to QQ Bot as a single comprehensive message.

## Core Rule: Title → Code Block per Item

Every item follows this pattern:

```
Plain text title/header
```详细说明
技术架构/方法
关键技术点
为什么值得关注
方向标签
```
```

## Per-Section Templates

### 🔥 GitHub Trending
```
【🔥 GitHub 今日热门】

1. owner/repo — ⭐XXk · language
```技术说明
项目是做什么的：具体解决什么问题、目标用户
技术架构：用到的技术栈、架构设计特点
关键技术点：用什么模型/框架/算法、设计亮点
为什么火：解决了什么普遍痛点、有什么创新
方向标签：[Edge AI / AI Agent / 机器人 / 小模型 / 边缘硬件 / 其他]
```

2. owner/repo — ⭐XXk · language
```技术说明
...
```
```

Requirements per code block: 5-8 lines minimum.

### 📄 Hugging Face Daily Papers
```
【📄 HF 每日论文】

Paper Title
```技术说明
研究的问题：这篇论文要解决什么问题、为什么重要
方法/架构：具体模型架构（Transformer/扩散/RNN? 参数规模?）、训练方式（预训练/微调/RL?）、关键技术
实验结果：什么数据集、什么指标、跟baseline比怎么样
核心创新点：跟已有工作比有什么本质不同
方向标签：[Edge AI / AI Agent / 机器人 / 小模型 / 边缘硬件 / 其他]
```
```

Requirements per code block: 6-10 lines minimum, must include method/architecture specifics.

### 💡 Hacker News
```
【💡 Hacker News 今日热点】

· Title (▲score)
```详细说明
内容概要：这篇文章/话题具体讲了什么
为什么上首页：技术亮点、争议点、行业影响
```

· Next Title (▲score)
```详细说明
...
```
```

Requirements per code block: 3-5 lines minimum.

### 📄 arXiv
```
【📄 arXiv 最新论文】

cs.AI: Paper Title
```技术说明
解决的问题、技术方法要点
```

cs.RO: Next Paper
```技术说明
...
```
```

### 🔧 Hackaday / 📦 Other Sources
Same pattern: title outside → code block inside with technical explanation.

### 📊 Key Repo Status
Simple table format, no code blocks needed:
```
【📊 关键仓库动态】

AI Agent方向
• owner/repo — ⭐XXk → one-line description
• owner/repo — ⭐XXk → description

Edge AI方向
• owner/repo — ⭐XXk → description
...
```

### 📊 Final Summary (300-500 words)
```
【📊 今日简报总结】

1. 今天信息最密集的方向 + 具体证据（哪些项目/论文/事件）
2. 该方向的技术趋势总结（不是罗列，提炼规律）
3. 其他方向值得注意的点
4. 技术分析——这些趋势说明了什么、对行业/用户的影响、建议关注的信号
```

## QQ Formatting Rules

1. **Each section header** uses bold emoji + text: `【🔥 GitHub 今日热门】`
2. **Each item** starts with plain text (title, stars, score), then the code block
3. **Code block delimiter**: Three backticks ` ``` ` on their own line before and after
4. **Inside code blocks**: Use concise structured labels (技术架构：/ 方法：/ 核心创新：) not prose paragraphs
5. **No markdown** outside code blocks — just plain text and emoji
6. **Mobile QQ truncates lines** longer than ~30-40 CJK characters — keep short
7. **All items shown**, no filtering by relevance

## Full Delivery Strategy

The cron job delivers ONE comprehensive message to QQ containing ALL categories. 
- `deliver: qqbot:CHANNEL_ID` in cronjob config
- The agent's final response IS the single message
- No send_message calls needed
- Result: ~16K chars, ~8 API calls, ~3 min runtime (with approvals.mode off)
