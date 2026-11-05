"""Fan-out search across providers with per-provider error isolation."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from omniref.models import (
    ProviderError,
    ProviderInfo,
    Reference,
    SearchRequest,
    SearchResponse,
)
from omniref.providers.base import ReferenceProvider

log = logging.getLogger(__name__)

DEFAULT_PROVIDER_TIMEOUT_S = 15.0


class ProviderRegistry:
    def __init__(
        self,
        providers: Iterable[ReferenceProvider] = (),
        provider_timeout_s: float = DEFAULT_PROVIDER_TIMEOUT_S,
    ) -> None:
        self._providers: dict[str, ReferenceProvider] = {}
        self._timeout = provider_timeout_s
        for p in providers:
            self.register(p)

    def register(self, provider: ReferenceProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def list(self) -> list[ProviderInfo]:
        return [p.info() for p in self._providers.values()]

    async def search(
        self, request: SearchRequest, providers: list[str] | None = None
    ) -> SearchResponse:
        if providers:
            unknown = sorted(set(providers) - self._providers.keys())
            if unknown:
                raise ValueError(
                    f"Unknown providers: {unknown}. Available: {sorted(self._providers)}"
                )
            selected = [self._providers[n] for n in dict.fromkeys(providers)]
        else:
            selected = list(self._providers.values())

        wanted = set(request.media_types)
        selected = [p for p in selected if p.media_types & wanted]

        outcomes = await asyncio.gather(*(self._run(p, request) for p in selected))

        errors = [
            ProviderError(provider=p.name, message=out)
            for p, out in zip(selected, outcomes, strict=True)
            if isinstance(out, str)
        ]
        per_provider = [out for out in outcomes if not isinstance(out, str)]

        return SearchResponse(
            query=request.query,
            results=_merge(per_provider, wanted),
            providers_queried=[p.name for p in selected],
            errors=errors,
        )

    async def _run(
        self, provider: ReferenceProvider, request: SearchRequest
    ) -> list[Reference] | str:
        """Return results, or an error message string. Never raises."""
        try:
            async with asyncio.timeout(self._timeout):
                return await provider.search(request)
        except TimeoutError:
            return f"timed out after {self._timeout}s"
        except Exception as exc:
            log.exception("provider %s failed", provider.name)
            return f"{type(exc).__name__}: {exc}"


def _merge(per_provider: list[list[Reference]], wanted: set) -> list[Reference]:
    """Round-robin interleave by provider rank, dedupe by URL, drop unwanted media types.

    Round-robin keeps one noisy provider from dominating the top of the list.
    Within a provider, original (relevance) order is preserved.
    """
    merged: list[Reference] = []
    seen_urls: set[str] = set()
    depth = max((len(r) for r in per_provider), default=0)
    for rank in range(depth):
        for results in per_provider:
            if rank >= len(results):
                continue
            ref = results[rank]
            if ref.media_type not in wanted or ref.url in seen_urls:
                continue
            seen_urls.add(ref.url)
            merged.append(ref)
    return merged
