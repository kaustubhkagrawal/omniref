"""Provider-agnostic data models.

Every provider maps its native payload into `Reference`, so agents see one
schema regardless of which search engine produced the result.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class Reference(BaseModel):
    """A single image or video reference, normalized across providers."""

    id: str = Field(
        description="Stable ID, prefixed with the provider name: '<provider>:<native_id>'."
    )
    provider: str = Field(description="Name of the provider that returned this result.")
    media_type: MediaType
    title: str
    url: str = Field(description="Direct URL to the media file or its canonical page.")
    page_url: str | None = Field(default=None, description="Human-facing page the media lives on.")
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = Field(default=None, description="Videos only.")
    license: str | None = Field(
        default=None, description="SPDX id or free-form license label, if known."
    )
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Provider-reported relevance, 0..1."
    )


class SearchRequest(BaseModel):
    """Normalized query passed to every provider."""

    query: str = Field(min_length=1)
    media_types: list[MediaType] = Field(default_factory=lambda: [MediaType.IMAGE, MediaType.VIDEO])
    limit: int = Field(default=10, ge=1, le=50, description="Max results per provider.")


class ProviderError(BaseModel):
    provider: str
    message: str


class SearchResponse(BaseModel):
    query: str
    results: list[Reference]
    providers_queried: list[str]
    errors: list[ProviderError] = Field(
        default_factory=list,
        description="Providers that failed. Partial results are still returned.",
    )


class ProviderInfo(BaseModel):
    name: str
    description: str
    media_types: list[MediaType]
    is_mock: bool = False
