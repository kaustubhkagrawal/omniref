import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from omniref.server import create_server


@pytest.fixture
async def client():
    async with Client(create_server()) as c:
        yield c


async def test_tools_are_exposed(client):
    names = {t.name for t in await client.list_tools()}
    assert names == {"list_providers", "search_references"}


async def test_search_returns_structured_normalized_results(client):
    res = await client.call_tool(
        "search_references", {"query": "rain", "media_types": ["video"], "limit": 3}
    )
    data = res.data
    assert data.query == "rain"
    assert len(data.results) == 6  # two mock providers x 3
    assert {r.media_type for r in data.results} == {"video"}
    assert data.errors == []


async def test_invalid_limit_is_rejected(client):
    with pytest.raises(ToolError):
        await client.call_tool("search_references", {"query": "x", "limit": 0})


async def test_unknown_provider_surfaces_as_tool_error(client):
    with pytest.raises(ToolError, match="Unknown providers"):
        await client.call_tool("search_references", {"query": "x", "providers": ["nope"]})
