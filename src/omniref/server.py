"""FastMCP server exposing the unified reference search."""

from __future__ import annotations

import argparse
from importlib.metadata import version
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from omniref.models import MediaType, ProviderInfo, SearchRequest, SearchResponse
from omniref.providers.mock import MockProvider
from omniref.registry import ProviderRegistry

INSTRUCTIONS = (
    "Search for image and video references to condition AI image/video generation "
    "(reference-to-video, style/character/motion references). One query fans out to "
    "multiple search providers and returns normalized results. Call list_providers "
    "first to see what is available."
)


def default_registry() -> ProviderRegistry:
    # Placeholder until real providers land. Two mocks exercise merge/dedupe paths.
    return ProviderRegistry(
        [
            MockProvider("mock-a"),
            MockProvider("mock-b", media_types=frozenset({MediaType.VIDEO})),
        ]
    )


def create_server(registry: ProviderRegistry | None = None) -> FastMCP:
    registry = registry or default_registry()
    mcp = FastMCP("omniref", instructions=INSTRUCTIONS)

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def list_providers() -> list[ProviderInfo]:
        """List configured reference search providers and the media types each supports."""
        return registry.list()

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def search_references(
        query: Annotated[
            str,
            Field(
                min_length=1,
                description="What to look for, e.g. 'handheld night street, neon, rain'.",
            ),
        ],
        media_types: Annotated[
            list[MediaType] | None,
            Field(description="Restrict to 'image' and/or 'video'. Default: both."),
        ] = None,
        providers: Annotated[
            list[str] | None,
            Field(description="Provider names from list_providers. Default: all."),
        ] = None,
        limit: Annotated[int, Field(ge=1, le=50, description="Max results per provider.")] = 10,
    ) -> SearchResponse:
        """Search images and videos across all providers; results are normalized and deduplicated.

        Partial failures are reported in `errors` while other providers' results are still returned.
        """
        request = SearchRequest(
            query=query,
            media_types=media_types or [MediaType.IMAGE, MediaType.VIDEO],
            limit=limit,
        )
        return await registry.search(request, providers)

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omniref",
        description="MCP server: unified image/video reference search for AI generation agents.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio (default, for clients that spawn the process) or http (streamable HTTP).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="http only. Default: 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8000, help="http only. Default: 8000.")
    parser.add_argument("--version", action="version", version=f"omniref {version('omniref')}")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    server = create_server()
    if args.transport == "stdio":
        # stdout carries the protocol; the banner would corrupt it.
        server.run(transport="stdio", show_banner=False)
    else:
        server.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
