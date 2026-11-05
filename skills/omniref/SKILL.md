---
name: omniref
description: Find image and video references for AI image/video generation (reference-to-video, style, character, motion, camera). Use when a user wants references, inspiration, or conditioning media for a generation prompt. Requires the omniref MCP server.
---

# omniref

Use the `omniref` MCP server to search many reference sources through one interface.

## Workflow

1. Call `list_providers` once to see which sources are configured and which media types each supports.
2. Turn the user's intent into a concrete visual query: subject, setting, lighting, camera movement, style. Prefer 3-8 descriptive words over a full sentence.
3. Call `search_references` with `query`. Narrow with `media_types` (`image`, `video`) and `providers` only when the user asks or the task clearly needs it (e.g. motion reference needs `video`).
4. Check `errors` in the response. Failed providers do not block others; mention them if results look thin.
5. Pick references by `license`, `width`/`height`, and `duration_seconds`. Prefer permissive licenses; surface `license` and `page_url` to the user so they can verify before use.

## Notes

- `id` is `<provider>:<native_id>` and stable across calls.
- Results are interleaved across providers and deduplicated by `url`.
- Providers flagged `is_mock: true` return fake data. Never present their results as real media.
