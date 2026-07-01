# Hermes Cronjob System — Full File Layout

When debugging a failed cronjob or explaining the system to a user, here is every file involved.

## File Tree

```
~/.hermes/
├── cron/
│   ├── jobs.json              ← CRONJOB DATABASE. Ground truth for all jobs.
│   │                              Fields: id, name, prompt, schedule, deliver,
│   │                              enabled_toolsets, state, last_status,
│   │                              last_run_at, last_delivery_error, next_run_at
│   ├── .tick.lock              ← Scheduler lock file. Prevents duplicate ticks.
│   └── output/
│       └── <job_id>/
│           └── YYYY-MM-DD_HH-MM-SS.md   ← Each run's output. Useful for
│                                            verifying content without re-running.
│
├── config.yaml                 ← TOP-LEVEL config. Keys used by cron:
│                                  model.default, model.provider, model.base_url
│                                  WEIXIN_HOME_CHANNEL, QQBOT_HOME_CHANNEL
│                                  approvals.mode (must be 'off' for autonomous cron)
│
├── .env                        ← API keys (DeepSeek etc.). Loaded at cron execution.
│
├── state.db                    ← Hermes SQLite state. Contains sessions, config cache.
│
├── weixin/
│   └── accounts/
│       ├── <id>.json           ← WeChat Bot account / auth token
│       ├── <id>.sync.json      ← Sync state
│       └── <id>.context-tokens.json  ← Conversation context tokens
│
└── logs/
    ├── gateway.log             ← DELIVERY LOGS. Check here when deliver fails:
    │                              "iLink sendmessage rate limited" = WeChat rate limit
    │                              "No home channel set" = stale config cache
    │                              "HTTP 402" = API key balance issue
    ├── agent.log               ← Agent session logs
    └── errors.log              ← Error aggregation

~/hermes-agent/cron/
├── scheduler.py                ← SCHEDULER DAEMON. Ticks every 60s, checks triggers.
│                                  Core loop: read jobs.json → find due jobs → execute.
├── jobs.py                     ← CRUD operations: create, update, pause, resume, remove, trigger.
└── __init__.py                 ← Module entry, exports public API.
```

## Key Diagnostic Paths

### "Cronjob ran but nothing delivered"
1. Check `~/.hermes/cron/output/<job_id>/` for the latest `.md` file → was output generated?
2. Check `~/.hermes/logs/gateway.log` for delivery errors → "rate limited" or "home channel"?
3. Run `cronjob(action='list')` → check `last_delivery_error` and `last_status`

### "send_message fails even though config.yaml has the right key"
- **Root cause**: Running CLI session caches config at startup. `hermes config set` writes to file but the in-memory cache is stale.
- **Fix**: The cronjob scheduler reads fresh config each tick — use the cronjob's `deliver` field instead of `send_message`. Or start a new session (`/new`).

### "Cronjob stalled / no output at all"
- **Likely**: Security approval blocked a command. Cron has no user to approve.
- **Check**: Is `approvals.mode: off` in config.yaml? Check `~/.hermes/logs/agent.log` for "Command requires approval" messages.
- **Fix**: `hermes config set approvals.mode off`

### "WeChat delivery keeps failing"
- **Check**: `~/.hermes/logs/gateway.log` → "rate limited" means iLink API limit hit (~4 sends/30s).
- **Workaround**: The cron auto-deliver handles one message per run. For multi-source briefings, all content goes in one final response.
- **Check credential validity**: `~/.hermes/weixin/accounts/` should have at least one `.json` file. If missing, re-auth via gateway QR login.

## Cronjob JSON Storage Format

The `jobs.json` file is the definitive source of truth. Always use `cronjob(action='list')` to read it; `jobs.json` fields include:

| Field | Example | Note |
|-------|---------|------|
| `id` | `72ecd70d04bd` | Internal ID |
| `name` | "每日信息简报" | Human-readable |
| `schedule.expr` | `"0 8 * * *"` | Cron expression |
| `deliver` | `"origin"` | Delivery target |
| `enabled_toolsets` | `["terminal", "web"]` | Tools the agent gets |
| `state` | `"scheduled"` | Lifecycle state |
| `last_delivery_error` | `"rate limited"` | Non-null when delivery failed |
| `prompt` | `(string, ~6-7KB)` | The full autonomous agent prompt |

The `prompt` field is the agent's task instruction — when a user asks "how does this work," read `jobs.json` to show the actual prompt verbatim.
