import sys

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from omniref.server import build_parser


def test_defaults_to_stdio():
    args = build_parser().parse_args([])
    assert args.transport == "stdio"


def test_http_flags_parse():
    args = build_parser().parse_args(["--transport", "http", "--host", "0.0.0.0", "--port", "9000"])
    assert (args.transport, args.host, args.port) == ("http", "0.0.0.0", 9000)


def test_unknown_transport_rejected():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--transport", "sse"])


async def test_stdio_subprocess_speaks_mcp_without_stdout_pollution():
    transport = StdioTransport(command=sys.executable, args=["-m", "omniref"])
    async with Client(transport) as c:
        res = await c.call_tool("search_references", {"query": "rain", "limit": 1})
        assert res.data.query == "rain"
        assert res.data.errors == []
