# omniref

One MCP interface to search image and video references across many search engines, built for AI image and video generation agents (reference-to-video, style, character and motion conditioning).

Status: pre-alpha. Only a deterministic mock provider exists today. The tool schema is the part to review.

## Run

Two transports, one binary. `stdio` is the default.

| Transport | Use when | Command |
| --- | --- | --- |
| `stdio` | The client spawns the server (Claude Desktop, Claude Code, Cursor) | `omniref` |
| `http` | Shared or remote server (streamable HTTP at `/mcp`) | `omniref --transport http --host 127.0.0.1 --port 8000` |

The HTTP server has no authentication. It binds to localhost by default; put it behind an authenticating proxy before exposing it. The Docker image binds `0.0.0.0` inside the container, so publish the port to `127.0.0.1` only (`-p 127.0.0.1:8000:8000`).

### From source

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run omniref                         # stdio
uv run omniref --transport http        # http://127.0.0.1:8000/mcp
```

### From a GitHub release

Each tag `vX.Y.Z` publishes a wheel and sdist on the [Releases page](https://github.com/kaustubhkagrawal/omniref/releases) and a container image on GHCR.

```bash
uvx --from https://github.com/kaustubhkagrawal/omniref/releases/download/v0.1.0/omniref-0.1.0-py3-none-any.whl omniref
docker run -i --rm ghcr.io/kaustubhkagrawal/omniref:0.1.0 --transport stdio
docker run --rm -p 127.0.0.1:8000:8000 ghcr.io/kaustubhkagrawal/omniref:0.1.0
```

### Connect a client

```bash
# stdio
claude mcp add omniref -- uvx --from git+https://github.com/kaustubhkagrawal/omniref omniref
# http
claude mcp add --transport http omniref http://127.0.0.1:8000/mcp
```

Generic stdio config (Claude Desktop, Cursor):

```json
{
  "mcpServers": {
    "omniref": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kaustubhkagrawal/omniref", "omniref"]
    }
  }
}
```

## Releasing

Bump `version` in `pyproject.toml`, merge to `main`, then `git tag vX.Y.Z && git push origin vX.Y.Z`. The release workflow checks the tag matches `pyproject.toml`, runs lint and tests, builds the artifacts, creates the GitHub Release, and pushes `ghcr.io/kaustubhkagrawal/omniref`. Tags with a hyphen (e.g. `v0.2.0-rc1`) are marked prerelease and do not move `latest`.

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
  server.py        FastMCP server and CLI (stdio + http)
  __main__.py      python -m omniref
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
