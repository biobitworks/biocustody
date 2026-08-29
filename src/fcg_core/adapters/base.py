"""Provider adapter contract — all adapters emit SourceOccurrence schema."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from fcg_core.identities import content_id, occurrence_id


class SourceOccurrence(BaseModel):
    schema_version: str = "1.0.0"
    provider: str
    content_id: str
    occurrence_id: str
    source_locator: str
    acquired_bytes_sha256: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    frozen_response_sha256: str | None = None


class ProviderAdapter(ABC):
    provider: str

    @abstractmethod
    def acquire(self, locator: str, *, actor_ref: str) -> SourceOccurrence:
        """ACQUIRE → exact bytes → SourceOccurrence. Network responses must be frozen offline."""


class LocalFileAdapter(ProviderAdapter):
    provider = "LOCAL_FILE"

    def acquire(self, locator: str, *, actor_ref: str) -> SourceOccurrence:
        from pathlib import Path

        raw = Path(locator).read_bytes()
        cid = content_id(raw)
        oid = occurrence_id(
            "fcg.source_occurrence.v1",
            cid,
            source_locator=f"file://{locator}",
            actor_ref=actor_ref,
            provider_ref=self.provider,
        )
        return SourceOccurrence(
            provider=self.provider,
            content_id=cid,
            occurrence_id=oid,
            source_locator=f"file://{locator}",
            acquired_bytes_sha256=cid,
        )


class FrozenHttpAdapter(ProviderAdapter):
    """Validate from frozen raw response bytes — never live HTTP as permanent validator input."""

    provider = "HTTP_FROZEN"

    def __init__(self, frozen_bytes: bytes, original_url: str) -> None:
        self._frozen = frozen_bytes
        self._url = original_url

    def acquire(self, locator: str, *, actor_ref: str) -> SourceOccurrence:
        cid = content_id(self._frozen)
        oid = occurrence_id(
            "fcg.source_occurrence.v1",
            cid,
            source_locator=self._url,
            actor_ref=actor_ref,
            provider_ref=self.provider,
            observation_context={"frozen_locator": locator},
        )
        return SourceOccurrence(
            provider=self.provider,
            content_id=cid,
            occurrence_id=oid,
            source_locator=self._url,
            acquired_bytes_sha256=cid,
            frozen_response_sha256=cid,
            metadata={"note": "offline frozen response; refresh creates successor occurrence"},
        )
