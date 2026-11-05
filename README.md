# omniref

One MCP interface to search image and video references across many search engines, built for AI image and video generation agents (reference-to-video, style, character and motion conditioning).

Status: pre-alpha. Only a deterministic mock provider exists today. The tool schema is the part to review.

## Run

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run omniref          # streamable HTTP on http://127.0.0.1:8000/mcp
HOST=0.0.0.0 PORT=9000 uv run omniref
```

The server has no authentication. It binds to localhost by default; put it behind an authenticating proxy before exposing it.

Connect a client:

```bash
claude mcp add --transport http omniref http://127.0.0.1:8000/mcp
```

## Tools

| Tool | Purpose |
| --- | --- |
| `list_providers` | Configured providers and the media types each supports |
| `search_references` | Fan out one query to all (or selected) providers; returns normalized, interleaved, URL-deduplicated results plus per-provider `errors` |

## Layout

```
src/omniref/
  models.py        Reference, SearchRequest, SearchResponse (the unified schema)
  registry.py      Parallel fan-out, timeouts, error isolation, merge/dedupe
  server.py        FastMCP server and HTTP entrypoint
  providers/
    base.py        ReferenceProvider interface
    mock.py        Fake data for dev and tests
skills/
  omniref/SKILL.md   Agent skill that teaches the workflow
tests/
```

## Adding a provider

Subclass `ReferenceProvider`, set `name`, `description`, `media_types`, implement `async search(request) -> list[Reference]`, and register it in `server.default_registry()`. Map the native payload into `Reference`; raise on failure and the registry reports it in `errors` without affecting other providers.

## Develop

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## License

MIT. See [LICENSE](LICENSE).
