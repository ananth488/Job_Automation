"""Base platform adapter interface with capabilities specification."""

from abc import ABC, abstractmethod
from typing import Any, TypedDict


class PlatformCapabilities(TypedDict):
    can_search: bool
    can_auto_apply: bool
    requires_browser: bool
    rate_limit_per_minute: int


class PlatformAdapter(ABC):
    """Abstract base class for all job board platform adapters."""

    def __init__(self, name: str, capabilities: PlatformCapabilities):
        self.name = name
        self.capabilities = capabilities

    @abstractmethod
    async def search_jobs(
        self,
        keywords: list[str],
        locations: list[str] | None = None,
        experience_min: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search jobs matching the criteria and return normalized job dicts."""
        pass

    @abstractmethod
    async def get_job_details(self, external_job_id: str) -> dict[str, Any] | None:
        """Fetch full details for a specific job."""
        pass

    @abstractmethod
    async def apply(
        self,
        external_job_id: str,
        application_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply to a job if supported, or raise error / prepare manual instructions."""
        pass

