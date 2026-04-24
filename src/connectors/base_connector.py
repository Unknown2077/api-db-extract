from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class FetchPage:
    records: list[dict]
    # Cursor string (GraphQL) or int offset (REST) — used to update checkpoint
    position: str | int
    is_last: bool


class BaseConnector(ABC):
    @property
    @abstractmethod
    def source_system(self) -> str: ...

    @abstractmethod
    def fetch_pages(self, start_position: str | int | None) -> Iterator[FetchPage]:
        """Yield pages of raw records starting from start_position.

        Args:
            start_position: Checkpoint cursor/offset to resume from.
                            None means start from the beginning.
        """
        ...
