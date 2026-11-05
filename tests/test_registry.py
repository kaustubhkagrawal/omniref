import asyncio

import pytest

from omniref import MediaType, ProviderRegistry, Reference, SearchRequest
from omniref.providers import MockProvider, ReferenceProvider


class FailingProvider(ReferenceProvider):
    name = "boom"
    description = "always fails"
    media_types = frozenset({MediaType.IMAGE, MediaType.VIDEO})

    async def search(self, request):
        raise RuntimeError("upstream 500")


class SlowProvider(ReferenceProvider):
    name = "slow"
    description = "never returns in time"
    media_types = frozenset({MediaType.IMAGE})

    async def search(self, request):
        await asyncio.sleep(10)
        return []


class FixedProvider(ReferenceProvider):
    description = "fixed results"
    media_types = frozenset({MediaType.IMAGE, MediaType.VIDEO})

    def __init__(self, name: str, refs: list[Reference]):
        self.name = name
        self._refs = refs

    async def search(self, request):
        return self._refs


def ref(provider: str, n: int, url: str | None = None, media=MediaType.IMAGE) -> Reference:
    return Reference(
        id=f"{provider}:{n}",
        provider=provider,
        media_type=media,
        title=f"{provider}-{n}",
        url=url or f"https://x.invalid/{provider}/{n}",
    )


async def test_failing_provider_does_not_hide_others():
    reg = ProviderRegistry([MockProvider("ok"), FailingProvider()])
    resp = await reg.search(SearchRequest(query="rain", limit=3))
    assert {r.provider for r in resp.results} == {"ok"}
    assert [(e.provider, "upstream 500" in e.message) for e in resp.errors] == [("boom", True)]
    assert resp.providers_queried == ["ok", "boom"]


async def test_slow_provider_times_out():
    reg = ProviderRegistry([MockProvider("ok"), SlowProvider()], provider_timeout_s=0.05)
    resp = await reg.search(SearchRequest(query="rain", media_types=[MediaType.IMAGE], limit=2))
    assert len(resp.results) == 2
    assert resp.errors[0].provider == "slow"
    assert "timed out" in resp.errors[0].message


async def test_providers_without_matching_media_type_are_skipped():
    reg = ProviderRegistry([MockProvider("img", media_types=frozenset({MediaType.IMAGE}))])
    resp = await reg.search(SearchRequest(query="x", media_types=[MediaType.VIDEO]))
    assert resp.providers_queried == []
    assert resp.results == []


async def test_results_interleave_round_robin_and_dedupe_by_url():
    shared = "https://x.invalid/shared"
    a = FixedProvider("a", [ref("a", 1), ref("a", 2, url=shared), ref("a", 3)])
    b = FixedProvider("b", [ref("b", 1, url=shared), ref("b", 2)])
    resp = await ProviderRegistry([a, b]).search(SearchRequest(query="x"))
    # rank0: a1, b1(shared, kept); rank1: a2(shared dup, dropped), b2; rank2: a3
    assert [r.id for r in resp.results] == ["a:1", "b:1", "b:2", "a:3"]


async def test_media_type_filter_drops_unrequested_results_from_mixed_providers():
    p = FixedProvider("p", [ref("p", 1), ref("p", 2, media=MediaType.VIDEO)])
    resp = await ProviderRegistry([p]).search(
        SearchRequest(query="x", media_types=[MediaType.VIDEO])
    )
    assert [r.id for r in resp.results] == ["p:2"]


async def test_unknown_provider_filter_raises_with_available_names():
    reg = ProviderRegistry([MockProvider("ok")])
    with pytest.raises(ValueError, match=r"Unknown providers: \['nope'\].*\['ok'\]"):
        await reg.search(SearchRequest(query="x"), providers=["nope"])


def test_duplicate_provider_name_rejected():
    with pytest.raises(ValueError, match="already registered"):
        ProviderRegistry([MockProvider("m"), MockProvider("m")])


async def test_mock_provider_is_deterministic():
    req = SearchRequest(query="neon street", limit=4)
    assert await MockProvider().search(req) == await MockProvider().search(req)
