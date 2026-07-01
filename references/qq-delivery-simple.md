# QQ Bot Delivery Notes for Daily Briefing

## Delivery Target

Cron job `deliver` field must use the **full channel ID**, not the bare platform name:

```
deliver: qqbot:YOUR_QQ_CHANNEL_ID
```

The scheduler delivers via "live adapter" — the same path the running gateway uses for outbound messages.

## Home Channel Fallback

If `deliver` is set to bare `qqbot` (no channel ID), the scheduler tries to resolve via `QQBOT_HOME_CHANNEL` config. If that's not set, delivery fails with "no delivery target resolved."

## Multi-Message Limitation

Cron jobs deliver exactly one message (the agent's final response). The agent inside the cron session does NOT reliably call `send_message` even when the `messaging` toolset is enabled.

## QQ Formatting (手机QQ)

- Code blocks (triple backticks) render as "小方框" — a bordered box with copy and fullscreen buttons
- Keep lines short — mobile QQ wraps at ~30-40 Chinese characters per line visually
- Use `---` or `━━━` separators between sections for visual clarity when sending one big message

## User Preferences (for this user)

- GitHub items: `序号. 项目名 — ⭐星数 · 语言 → 一句话简介` (compact, one per line)
- HF papers: title + summary outside, detailed code block inside per paper
- HN: title + score outside, code block with "what and why" inside per item
- All sources use code blocks for detailed content
- Final message: summary of today's trends + agent's thoughts
- Show ALL items, no filtering by relevance
