# MCP registry census — 2026-11-13

A complete crawl of the official Model Context Protocol registry
(`https://registry.modelcontextprotocol.io/v0/servers`), taken on 2026-11-13 between
11:31 and 13:11 UTC. Every page of every namespace, no filtering.

## Headline numbers

| Metric | Value |
|---|---|
| Published versions scanned | **250,478** |
| Distinct servers (unique names) | **63,364** |
| Mean versions per server | 3.95 |
| Served as remote endpoint (streamable HTTP / SSE) | 42,732 (67.4%) |
| Package-only (npx / uvx / docker) | 19,929 (31.5%) |
| No transport declared | 703 (1.1%) |
| Marked `deprecated` | 1,001 |
| Servers under `io.github.*` | 35,590 (56.2%) across 17,240 GitHub accounts |
| Largest single publisher | `io.github.sadri-dridi` — 2,366 servers |
| Largest single server by version count | `io.github.brilliantdirectories/brilliant-directories-mcp` — 1,211 versions |

The registry is not a list of products, it is a list of publications: 3.95 versions per
name on average, and a long tail of publishers who push a version per commit. Search in the
registry matches the **server name**, so a name without a clear noun is effectively invisible
no matter how good the description is.

## Files

- `data/servers.csv.gz` — every distinct `(name, version)` pair: 250,478 rows, columns
  `name, version, status, has_remote, has_package, updated_at`. 2 MB compressed.
- `data/census-aggregates.json` — the aggregates behind the table above (namespace
  concentration, transport split, category mentions, top publishers).
- `data/census.ndjson.gz` — the raw API rows as returned, one JSON object per line. 10 MB
  compressed, 112 MB uncompressed.
- `scripts/fetch_registry.py` — the crawler. Resumable: writes a cursor file, appends to
  ndjson, stops cleanly on `end of registry (no nextCursor)`.

## Reproduce

```bash
python3 scripts/fetch_registry.py 3000   # page cap; 2,336 pages were needed
python3 scripts/stats.py                 # writes census-aggregates.json
```

Crawl cost: 2,336 requests, ~100 minutes at ~2.5 s per 100-row page. The API is
cursor-paginated and the cursor is `name:version`, so it survives interrupted runs.

## Caveats

- A point-in-time snapshot. The registry accepts new versions continuously, so re-running the
  crawler on another day will show a larger number.
- "Distinct servers" = distinct registry names. One product publishing under two names counts
  twice.
- Category mentions are keyword matches over name + description, not registry metadata; they
  overlap and are indicative, not authoritative.

Prepared by [McpStamp](https://www.mcpstamp.com/research/mcp-registry-census/) — 58 hosted
MCP servers, 7th largest publisher in this census.
