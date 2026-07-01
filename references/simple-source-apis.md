# Information Source APIs

Working endpoints and scraping commands for daily info briefing. All commands assume proxy is set via `export https_proxy=$PROXY_URL`.

## GitHub Trending

**URL:** https://github.com/trending?since=daily
**Method:** HTML parsing (static page, no API)
**Reliability:** ⭐⭐⭐

```bash
curl -sL --proxy $PROXY_URL https://github.com/trending?since=daily
```

Parse with Python regex:
```python
import re
# Extract repo name + path
repos = re.findall(r'<h2[^>]*class=\"[^\"]*h3[^\"]*\"[^>]*>.*?<a href=\"/trending[^\"]*\"[^>]*>([^<]+)</a>.*?<a href=\"/([^\"]+)\"', content)
# Extract descriptions (same order as repos)
descs = re.findall(r'<p class=\"col-9[^\"]*color-fg-muted[^\"]*\"[^>]*>\s*(.*?)\s*</p>', content, re.DOTALL)
```

**Notes:** ~25 repos per page. HTML structure is stable but has no guarantee. Filter by star count to keep quality high.

## Hugging Face Daily Papers

**URL:** https://huggingface.co/api/daily_papers
**Method:** JSON API — returns array of paper objects
**Reliability:** ⭐⭐⭐⭐⭐ (official API)

```bash
curl -s --proxy $PROXY_URL 'https://huggingface.co/api/daily_papers?limit=10'
```

Response structure: array of objects with `title`, `authors`, `summary`, `url`, `paper_id` fields. No auth needed.
Default returns ~10 papers. Use `limit` param for more.

## Hacker News

**URL (top stories):** https://hacker-news.firebaseio.com/v0/topstories.json
**URL (item detail):** https://hacker-news.firebaseio.com/v0/item/{id}.json
**Method:** Firebase REST API — no auth needed
**Reliability:** ⭐⭐⭐⭐⭐

```bash
# Get top 100 story IDs
curl -s --proxy $PROXY_URL 'https://hacker-news.firebaseio.com/v0/topstories.json'
# Get details for each
curl -s --proxy $PROXY_URL 'https://hacker-news.firebaseio.com/v0/item/12345.json'
```

Item response includes: `title`, `score`, `by`, `url`, `descendants` (comment count), `time` (unix timestamp).
Limit to top 10-15 stories by slicing the ID array. Use `topstories` (hot), `newstories` (latest), or `beststories` (best).

## arXiv

**URL:** https://export.arxiv.org/api/query
**Method:** Atom XML API
**Reliability:** ⭐⭐ (sometimes times out via proxy)

```bash
curl -sL --proxy $PROXY_URL \
  'https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=5'
```

**Categories:** cs.AI (AI), cs.LG (Machine Learning), cs.RO (Robotics), cs.CL (Computation & Language), cs.CV (Computer Vision)
**Fallback:** Set short timeout (10s) and skip on failure. The API is flaky behind proxies.

## Reddit r/MachineLearning

**URL (old.reddit.com JSON):** https://old.reddit.com/r/MachineLearning/hot/.json
**URL (new API):** https://www.reddit.com/r/MachineLearning/hot.json
**Method:** JSON API — needs User-Agent header
**Reliability:** ⭐ (frequently blocked by Cloudflare/rate limits from proxy IPs)

```bash
curl -s --proxy $PROXY_URL \
  -H 'User-Agent: Mozilla/5.0 (compatible)' \
  'https://old.reddit.com/r/MachineLearning/hot/.json?limit=10'
```

**Notes:** Often returns Cloudflare challenge page instead of JSON. Treat as bonus source — never rely on it.
Rate limit: ~60 req/min per IP. Proxy IPs are often already flagged.

## IEEE Spectrum Robotics (weekly)

**URL:** https://spectrum.ieee.org/topic/robotics/
**Method:** HTML scraping
**Reliability:** ⭐⭐

Not implemented yet in the initial build. Requires regex parsing of article cards.
