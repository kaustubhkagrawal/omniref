"""Provider interface. Implement this to plug in a new search engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from omniref.models import MediaType, ProviderInfo, Reference, SearchRequest


class ReferenceProvider(ABC):
    #: Unique, lowercase, used as the ID prefix and in `providers=` filters.
    name: str
    description: str
    media_types: frozenset[MediaType]
    is_mock: bool = False

    @abstractmethod
    async def search(self, request: SearchRequest) -> list[Reference]:
        """Return up to `request.limit` references.

        Only called when `request.media_types` intersects `self.media_types`.
        Raise on failure; the registry isolates errors per provider.
        """

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            description=self.description,
            media_types=sorted(self.media_types),
            is_mock=self.is_mock,
        )
