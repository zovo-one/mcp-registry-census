#!/usr/bin/env python3
"""Analyse the MCP registry census ndjson -> stats.json for the public study page."""
import json, os, re, sys
from collections import Counter, defaultdict

SRC = os.path.expanduser("~/mcp-servers/data/s1112/census.ndjson")
OUT = os.path.expanduser("~/mcp-servers/data/s1112/census_stats.json")

rows = {}
for line in open(SRC):
    try:
        r = json.loads(line)
    except Exception:
        continue
    k = (r["name"], r.get("version"))
    rows[k] = r
rows = list(rows.values())
latest = {}
for r in rows:
    n = r["name"]
    if n not in latest or str(r.get("publishedAt") or "") > str(latest[n].get("publishedAt") or ""):
        latest[n] = r
servers = list(latest.values())

def ns(name):
    return name.split("/")[0] if "/" in name else name

ns_counter = Counter(ns(s["name"]) for s in servers)
files = Counter(ns(s["name"]).split(".")[0] for s in servers)
github_ns = ns_counter.get("io.github", 0) + 0
# io.github.<user>/<repo>
def gh_user(name):
    m = re.match(r"^io\.github\.([^/]+)/", name)
    return m.group(1) if m else None
gh_users = Counter(gh_user(s["name"]) for s in servers if gh_user(s["name"]))
no_desc = sum(1 for s in servers if not (s.get("description") or "").strip())
short_desc = sum(1 for s in servers if 0 < len(s.get("description") or "") < 40)
remote_only = sum(1 for s in servers if s.get("remotes") and not s.get("packages"))
pkg_only = sum(1 for s in servers if s.get("packages") and not s.get("remotes"))
both = sum(1 for s in servers if s.get("packages") and s.get("remotes"))
neither = sum(1 for s in servers if not s.get("packages") and not s.get("remotes"))
vers = Counter(s["name"] for s in rows)
top_versions = vers.most_common(15)
status = Counter((s.get("status") or "unknown") for s in servers)
total_rows = len(rows)
total_servers = len(servers)

words = Counter()
stop = set("the a an and or of for to in on with your you our is are can all any from by at as it this that be use using via mcp server servers tool tools api app".split())
cats = {
    "finance/invoicing": ["invoice", "payment", "billing", "bank", "vat", "tax", "accounting", "expense", "payroll", "stripe", "crypto", "trading", "stock", "currency"],
    "documents/pdf": ["pdf", "docx", "document", "ocr", "markdown", "spreadsheet", "csv", "excel", "file"],
    "dev/code": ["code", "github", "gitlab", "repo", "deploy", "ci", "build", "docker", "kubernetes", "npm", "debug", "typescript"],
    "data/db": ["database", "sql", "postgres", "mysql", "sqlite", "mongo", "query", "dataset", "analytics"],
    "search/web": ["search", "web", "crawl", "scrape", "browser", "serp", "news", "rss"],
    "ai/media": ["image", "video", "audio", "transcribe", "tts", "speech", "llm", "embedding", "vector", "model"],
    "comms": ["email", "slack", "discord", "telegram", "whatsapp", "sms", "chat", "calendar", "meeting"],
    "cloud/infra": ["aws", "azure", "gcp", "cloudflare", "s3", "server", "monitor", "log", "metrics", "docker"],
}
cat_counts = Counter()
for s in servers:
    text = ((s.get("title") or "") + " " + (s.get("description") or "")).lower()
    hit = False
    for c, kws in cats.items():
        if any(k in text for k in kws):
            cat_counts[c] += 1
            hit = True
    if not hit:
        cat_counts["other"] += 1

stats = {
    "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "rows_scanned": total_rows,
    "distinct_servers": total_servers,
    "versions_per_server_mean": round(total_rows / max(total_servers, 1), 2),
    "servers_with_no_description": no_desc,
    "servers_with_tiny_description": short_desc,
    "transport": {"remote_only": remote_only, "package_only": pkg_only, "both": both, "neither": neither},
    "status": dict(status),
    "top_namespaces": ns_counter.most_common(15),
    "namespace_families": files.most_common(12),
    "github_users_top": gh_users.most_common(15),
    "github_servers": sum(gh_users.values()),
    "distinct_github_publishers": len(gh_users),
    "top_version_spam": [{"name": n, "versions": c} for n, c in top_versions],
    "category_mentions": cat_counts.most_common(),
}
json.dump(stats, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in stats.items() if k not in ("top_namespaces", "github_users_top", "top_version_spam")}, indent=1)[:2500])
print("top namespaces:", stats["top_namespaces"][:8])
print("version spam:", stats["top_version_spam"][:5])
