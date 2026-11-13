#!/usr/bin/env python3
"""Resumable full pagination of the official MCP registry (v0/servers).

Writes newline-delimited JSON rows to census.ndjson and the cursor to census.cursor.
Re-run to resume. Stops when nextCursor is absent or the name sort reaches 'zzz'.
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = "https://registry.modelcontextprotocol.io/v0/servers"
OUT = os.path.expanduser("~/mcp-servers/data/s1112/census.ndjson")
CUR = os.path.expanduser("~/mcp-servers/data/s1112/census.cursor")
CAP_PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 500

cursor = None
if os.path.exists(CUR):
    cursor = open(CUR).read().strip() or None
seen = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        for line in f:
            try:
                r = json.loads(line)
                seen.add((r["name"], r.get("version")))
            except Exception:
                pass

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 zovo-census"})
    return json.loads(urllib.request.urlopen(req, timeout=90).read())

pages = 0
added = 0
t0 = time.time()
with open(OUT, "a") as fh:
    while pages < CAP_PAGES:
        u = BASE + "?limit=100" + (("&cursor=" + urllib.parse.quote(cursor)) if cursor else "")
        try:
            d = get(u)
        except Exception as e:
            print("ERR page %d: %s" % (pages, e)); time.sleep(3); continue
        srv = d.get("servers", [])
        if not srv:
            print("empty page, stopping"); break
        for x in srv:
            s = x.get("server", {})
            row = {
                "name": s.get("name"),
                "version": s.get("version"),
                "title": s.get("title"),
                "description": (s.get("description") or "")[:400],
                "desc_len": len(s.get("description") or ""),
                "website": s.get("websiteUrl"),
                "remotes": len(s.get("remotes") or []),
                "packages": len(s.get("packages") or []),
                "repo": (s.get("repository") or {}).get("url"),
                "status": ((x.get("_meta") or {}).get("io.modelcontextprotocol.registry/official") or {}).get("status"),
                "publishedAt": ((x.get("_meta") or {}).get("io.modelcontextprotocol.registry/official") or {}).get("publishedAt"),
                "isLatest": ((x.get("_meta") or {}).get("io.modelcontextprotocol.registry/official") or {}).get("isLatest"),
            }
            k = (row["name"], row["version"])
            if k in seen:
                continue
            seen.add(k)
            fh.write(json.dumps(row) + "\n")
            added += 1
        fh.flush()
        nxt = (d.get("metadata") or {}).get("nextCursor")
        pages += 1
        if pages % 20 == 0:
            print("pages %d rows %d elapsed %.0fs last=%s" % (pages, len(seen), time.time() - t0, srv[-1]["server"]["name"]), flush=True)
        if not nxt:
            print("end of registry (no nextCursor)"); open(CUR, "w").write(""); break
        cursor = nxt
        open(CUR, "w").write(cursor)
        if srv[-1]["server"]["name"] > "zzz":
            print("reached zzz"); break
print("done pages=%d added=%d total_unique=%d" % (pages, added, len(seen)))
