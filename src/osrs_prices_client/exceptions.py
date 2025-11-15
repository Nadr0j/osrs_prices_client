"""Custom exceptions for the OSRS prices client."""

from __future__ import annotations

from typing import Iterable, Tuple


class InvalidItemIdError(ValueError):
    """Raised when a request references item IDs that are not in the mapping endpoint."""

    def __init__(self, invalid_item_ids: Iterable[str]):
        sorted_ids = tuple(sorted(invalid_item_ids))
        message = f"Invalid item IDs requested: {', '.join(sorted_ids)}"
        super().__init__(message)
        self.invalid_item_ids: Tuple[str, ...] = sorted_ids
