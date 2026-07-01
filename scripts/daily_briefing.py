#!/usr/bin/env python3
"""Daily tech news briefing - standalone script, no LLM involvement.

Usage:
    python3 scripts/daily_briefing.py

Starts proxy for foreign sources, fetches data, composes briefing,
sends to configured channels, stops proxy.

Environment variables (set in shell or .env file):
    FEISHU_APP_ID       - Feishu app ID
    FEISHU_APP_SECRET   - Feishu app secret
    FEISHU_HOME_CHANNEL - Feishu chat_id (e.g. oc_xxxxx)

Proxy configuration:
    Set PROXY_URL env var to your proxy address
"""
import os, sys, json, re, time, subprocess, shutil
from datetime import datetime

try:
    import requests
except ImportError:
    print("pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Config (override via env vars) ─────────────────────────────────
PROXY_BIN = os.environ.get('PROXY_BIN', '')
PROXY_DIR = os.environ.get('PROXY_DIR', '')
ENV_PATH = os.environ.get('HERMES_ENV', os.path.expanduser('~/.hermes/.env'))
PROXY = {
    'http': os.environ.get('PROXY_URL', ''),
    'https': os.environ.get('PROXY_URL', ''),
}
PROXY_URL = os.environ.get('PROXY_URL', '')
OUTPUT_FILE = os.environ.get('BRIEFING_OUTPUT', '/tmp/hermes_briefing.txt')


def load_env():
    """Load .env file if it exists."""
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def proxy_start():
    """Start proxy if not already running. Returns True if proxy is ready."""
    if not shutil.which(PROXY_BIN.split()[0]) and not os.path.exists(PROXY_BIN):
        print(f"Proxy binary not found: {PROXY_BIN}", file=sys.stderr)
        return False
    proxy_name = os.path.basename(PROXY_BIN) if PROXY_BIN else ''
    p = subprocess.run(['pgrep', proxy_name], capture_output=True) if proxy_name else subprocess.CompletedProcess([], 1)
    if p.returncode == 0:
        return True  # already running
    subprocess.Popen([PROXY_BIN, '-d', PROXY_DIR],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    p = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
    port = PROXY_URL.split(':')[-1]
    if port in p.stdout:
        return True
    print("Proxy start failed", file=sys.stderr)
    return False


def proxy_stop():
    """Stop proxy."""
    subprocess.run(['pkill', proxy_name], capture_output=True) if proxy_name else None


def fetch(url, use_proxy=False, timeout=15):
    """Fetch URL content. Returns text or None on failure."""
    try:
        p = PROXY if use_proxy else None
        r = requests.get(
            url, timeout=timeout, proxies=p,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        )
        return r.text if r.ok else None
    except Exception:
        return None


def collect_github_trending(proxy_ok):
    """Collect GitHub trending repos via Search API."""
    today = datetime.now().strftime('%Y-%m-%d')
    # Use 7-day window for more results
    from datetime import timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    text = fetch(
        f'https://api.github.com/search/repositories?q=created:>{week_ago}&sort=stars&order=desc&per_page=25',
        use_proxy=False  # GitHub API: direct connection avoids rate limits on proxy IP
    )
    if not text:
        # Fallback: try with proxy
        text = fetch(
            f'https://api.github.com/search/repositories?q=created:>{week_ago}&sort=stars&order=desc&per_page=25',
            use_proxy=proxy_ok
        )
    if text:
        try:
            items = json.loads(text).get('items', [])
            return [
                f"• {i['full_name']} ⭐{i['stargazers_count']} ({i.get('language', 'N/A')})\n  {(i.get('description') or '')[:120]}"
                for i in items[:15]
            ]
        except (json.JSONDecodeError, KeyError):
            pass
    return []


def collect_hackernews(proxy_ok):
    """Collect top Hacker News stories."""
    text = fetch('https://hacker-news.firebaseio.com/v0/topstories.json', use_proxy=proxy_ok)
    if not text:
        return []
    try:
        ids = json.loads(text)[:10]
    except json.JSONDecodeError:
        return []
    items = []
    for sid in ids:
        t = fetch(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', use_proxy=proxy_ok, timeout=8)
        if t:
            try:
                item = json.loads(t)
                items.append(f"• {item.get('title', '')} (💡{item.get('score', 0)})")
            except json.JSONDecodeError:
                pass
    return items


def collect_arxiv(proxy_ok, categories=None):
    """Collect latest arXiv papers for given categories."""
    if categories is None:
        categories = ['cs.AI', 'cs.LG', 'cs.RO', 'cs.CL']
    items = []
    for cat in categories:
        text = fetch(
            f'http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=3',
            use_proxy=proxy_ok
        )
        if text:
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in root.findall('atom:entry', ns):
                    title_el = entry.find('atom:title', ns)
                    if title_el is not None and title_el.text:
                        items.append(f"[{cat}] {title_el.text.strip()[:150]}")
            except ET.ParseError:
                pass
    return items


def collect_hackaday(proxy_ok):
    """Collect Hackaday articles."""
    text = fetch('https://hackaday.com/blog/', use_proxy=proxy_ok)
    if text:
        titles = re.findall(r'entry-title[^>]*>(.*?)</', text, re.DOTALL)
        return [f"• {re.sub(r'<[^>]+>', '', t).strip()[:120]}" for t in titles[:8]]
    return []


def collect_hf_papers(proxy_ok):
    """Collect Hugging Face Daily Papers."""
    text = fetch('https://huggingface.co/api/daily_papers', use_proxy=proxy_ok)
    if text:
        try:
            papers = json.loads(text)
            return [
                f"• {p.get('title', '')[:100]}"
                for p in papers[:10]
            ]
        except json.JSONDecodeError:
            pass
    return []


def collect_ollama(proxy_ok):
    """Collect trending Ollama models."""
    text = fetch('https://ollama.com/library', use_proxy=proxy_ok)
    if text:
        # Try model title attribute first (more reliable)
        models = re.findall(r'x-test-model-title[^>]*title="([^"]+)"', text)
        if not models:
            # Fallback: href extraction
            models = re.findall(r'href="/library/([^"/]+)"', text)
        seen = set()
        result = []
        for m in models:
            if m not in seen:
                seen.add(m)
                result.append(f"• {m}")
        return result[:10]
    return []


def collect_edge_impulse(proxy_ok):
    """Collect Edge Impulse blog posts via RSS."""
    text = fetch('https://www.edgeimpulse.com/blog/category/all/rss/', use_proxy=proxy_ok)
    if text:
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            items = []
            for entry in root.findall('.//atom:entry', ns)[:6]:
                title = entry.find('atom:title', ns)
                if title is not None and title.text:
                    items.append(f"• {title.text.strip()[:120]}")
            return items
        except ET.ParseError:
            pass
    return []


def collect_anthropic(proxy_ok):
    """Collect Anthropic news headlines."""
    text = fetch('https://www.anthropic.com/news', use_proxy=proxy_ok)
    if text:
        # Combined h2 + h4 extraction
        titles = re.findall(r'<h[24][^>]*>(.*?)</h[24]>', text, re.DOTALL)
        result = []
        seen = set()
        for t in titles:
            clean = re.sub(r'<[^>]+>', '', t).strip()[:150]
            if clean and len(clean) > 5 and clean not in seen:
                # Filter out navigation text
                if not any(skip in clean.lower() for skip in ['menu', 'nav', 'footer', 'header', 'featured']):
                    seen.add(clean)
                    result.append(f"• {clean}")
        return result[:6]
    return []


def collect_news():
    """Collect from all sources. Returns dict of section_name -> items."""
    sections = {}
    proxy_ok = proxy_start()

    collectors = {
        '📌 GitHub Trending': lambda: collect_github_trending(proxy_ok),
        '📄 HuggingFace Daily Papers': lambda: collect_hf_papers(proxy_ok),
        '💡 Hacker News': lambda: collect_hackernews(proxy_ok),
        '📄 arXiv 最新论文': lambda: collect_arxiv(proxy_ok),
        '🔧 Hackaday': lambda: collect_hackaday(proxy_ok),
        '📦 Ollama 新模型': lambda: collect_ollama(proxy_ok),
        '📡 Edge Impulse': lambda: collect_edge_impulse(proxy_ok),
        '🤖 Anthropic': lambda: collect_anthropic(proxy_ok),
    }

    for name, fn in collectors.items():
        try:
            items = fn()
            if items:
                sections[name] = items
            else:
                sections[name] = ['[DATA FAILED]']
        except Exception as e:
            sections[name] = [f'[DATA FAILED: {e}]']

    proxy_stop()
    return sections


def build_message(sections):
    """Build formatted briefing message."""
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📡 技术简报 | {today}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    for name, items in sections.items():
        lines.append(f"\n{name}")
        lines.extend(items)

    # Summary
    success = sum(1 for v in sections.values() if v and v[0] != '[DATA FAILED]')
    total = len(sections)
    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 数据覆盖：{success}/{total} 源成功")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🤖 by Hermes Agent")

    return "\n".join(lines)


def send_feishu(msg):
    """Send message to Feishu via API."""
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    chat_id = os.environ.get('FEISHU_HOME_CHANNEL')
    if not app_id or not app_secret or not chat_id:
        print("Feishu env vars not set (FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_HOME_CHANNEL)",
              file=sys.stderr)
        return False
    try:
        r = requests.post(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            json={'app_id': app_id, 'app_secret': app_secret}
        )
        token = r.json().get('tenant_access_token')
        if not token:
            print("Feishu auth failed", file=sys.stderr)
            return False
        requests.post(
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'receive_id': chat_id, 'msg_type': 'text',
                  'content': json.dumps({'text': msg})}
        )
        return True
    except Exception as e:
        print(f"Feishu send failed: {e}", file=sys.stderr)
        return False


def main():
    load_env()
    sections = collect_news()
    msg = build_message(sections)
    print(msg)

    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(msg)
    print(f"\nSaved to {OUTPUT_FILE}", file=sys.stderr)

    # Send to Feishu if configured
    send_feishu(msg)


if __name__ == '__main__':
    main()
