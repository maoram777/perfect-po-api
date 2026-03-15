"""Application-specific exceptions."""

from typing import List


class MissingCatalogHeadersError(Exception):
    """Raised when a catalog file (CSV/Excel) is missing required column headers."""

    def __init__(self, missing_headers: List[str], file_type: str = "file"):
        self.missing_headers = list(missing_headers)
        self.file_type = file_type
        super().__init__(f"Missing required {file_type} headers: {', '.join(self.missing_headers)}")
