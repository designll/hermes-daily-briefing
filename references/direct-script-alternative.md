# Direct Fetch-Script Alternative (No LLM Assembly)

When the cron job's LLM assembly step fails repeatedly (e.g., DeepSeek stale stream timeout), use a standalone Python script that fetches all sources and composes the briefing text directly, without calling any LLM API.

## When to Use

- The cron job fails with `Stream stale for 180s` mid-assembly
- DeepSeek API is intermittently unavailable
- User just wants the data assembled reliably without AI summarization

## Implementation

The script in `scripts/daily_briefing.py` does the full workflow:

1. Starts proxy (if needed for foreign sources)
2. Fetches from 5+ sources via `requests.get()`
3. Composes plain text briefing
4. Sends to Feishu/QQ via direct API calls (no send_message tool)
5. Stops proxy

Key design decisions:
- **No LLM involvement** — avoids stale-stream failures entirely
- **Direct API send** — bypasses `send_message` tool's env-var dependency issue
- **Proxy on-demand** — starts proxy only for foreign sources, stops after
- **Graceful degradation** — failed sources get silently skipped

## Integration with Cron

To use this as the cron job's handler instead of the default LLM-prompt approach:

Option A: Replace the cron job's prompt with a script-only run instruction
Option B: Set the cron job's `script` parameter to point to `scripts/daily_briefing.py` with `no_agent=True` (scheduled, no LLM involvement at all).

For Option B, the cron command would reference the script directly:
```bash
cronjob(action='create', schedule='0 8 * * *', script='scripts/daily_briefing.py', no_agent=True)
```

The script's stdout is delivered verbatim — so the script needs to output the briefing text.

## Sources Fetched

| Source | Method | Proxy Needed |
|--------|--------|-------------|
| GitHub Trending (Search API) | JSON API | ✅ Yes |
| Hacker News | Firebase API | ✅ Yes |
| ArXiv | Atom XML | ✅ Yes |
| V2EX | JSON API | ✅ Yes |
| 36氪 | HTML scrape (site name only) | ❌ No JS content |
| 机器之心 | HTML scrape (site name only) | ❌ No JS content |
| 量子位 | HTML scrape (site name only) | ❌ No JS content |
| 雷锋网 | HTML scrape (site name only) | ❌ No JS content |
| 开源中国 | HTML scrape (site name only) | ❌ No JS content |

**Note:** Chinese tech sites return JS-rendered content that curl can't extract. The script gets site names only from those sources. For real article titles from Chinese sources, use RSS/API endpoints or browser automation instead.

## Sending to Feishu

The script calls the Feishu API directly (not via `send_message` tool):

```python
resp = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': app_id, 'app_secret': app_secret})
token = resp.json()['tenant_access_token']

requests.post(
    'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
    headers={'Authorization': f'Bearer {token}'},
    json={'receive_id': 'oc_xxxx', 'msg_type': 'text',
          'content': json.dumps({'text': briefing_text})}
)
```

This avoids the `send_message` tool's env-var dependency (it needs FEISHU_APP_ID/FEISHU_APP_SECRET in the process environment, not just in `.env`).
