"""Deterministic fake provider used for development and tests. No network."""

from __future__ import annotations

import hashlib

from omniref.models import MediaType, Reference, SearchRequest
from omniref.providers.base import ReferenceProvider


class MockProvider(ReferenceProvider):
    description = "Deterministic fake results for development and tests. Not real media."
    is_mock = True

    def __init__(
        self,
        name: str = "mock",
        media_types: frozenset[MediaType] = frozenset({MediaType.IMAGE, MediaType.VIDEO}),
    ) -> None:
        self.name = name
        self.media_types = media_types

    async def search(self, request: SearchRequest) -> list[Reference]:
        wanted = [m for m in request.media_types if m in self.media_types]
        results: list[Reference] = []
        for i in range(request.limit):
            media_type = wanted[i % len(wanted)]
            digest = hashlib.sha1(f"{self.name}|{request.query}|{i}".encode()).hexdigest()[:10]
            native_id = f"{media_type.value}-{digest}"
            is_video = media_type is MediaType.VIDEO
            results.append(
                Reference(
                    id=f"{self.name}:{native_id}",
                    provider=self.name,
                    media_type=media_type,
                    title=f"{request.query} ({media_type.value} #{i + 1})",
                    url=f"https://example.invalid/{self.name}/{native_id}",
                    page_url=f"https://example.invalid/{self.name}/page/{native_id}",
                    thumbnail_url=f"https://example.invalid/{self.name}/thumb/{native_id}.jpg",
                    width=1920 if is_video else 1024,
                    height=1080 if is_video else 768,
                    duration_seconds=8.0 + i if is_video else None,
                    license="CC0-1.0",
                    author="mock-author",
                    tags=request.query.lower().split()[:5],
                    score=round(max(0.0, 1.0 - i * 0.05), 2),
                )
            )
        return results
