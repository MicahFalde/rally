import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator

from app.models import Voter


class StateAdapter(ABC):
    """Base class for state-specific voter file parsers.

    Each state's voter file has a different format, column names, and encoding.
    Subclass this for each state you support.
    """

    @property
    @abstractmethod
    def state_code(self) -> str:
        """Two-letter state code, e.g. 'OH'."""
        ...

    @property
    @abstractmethod
    def file_encoding(self) -> str:
        """File encoding, e.g. 'utf-8', 'latin-1'."""
        ...

    @property
    @abstractmethod
    def delimiter(self) -> str:
        """CSV delimiter, e.g. ',' or '|' or '\\t'."""
        ...

    @abstractmethod
    def parse_row(self, row: dict) -> dict:
        """Parse a single CSV row into a dict matching Voter model fields.

        Returns a dict with keys matching Voter column names.
        Must include at minimum: state_voter_id, first_name, last_name,
        address_line1, city, state_code, zip_code.
        """
        ...

    def parse_file(self, file_path: str | Path) -> list[dict]:
        """Parse a voter file and yield dicts ready for Voter model creation."""
        file_path = Path(file_path)
        records = []

        with open(file_path, encoding=self.file_encoding, errors="replace") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                try:
                    parsed = self.parse_row(row)
                    if parsed:
                        parsed["state"] = self.state_code
                        records.append(parsed)
                except Exception:
                    # Skip malformed rows — log in production
                    continue

        return records

    def normalize_party(self, raw: str | None) -> str | None:
        """Normalize party registration to standard codes."""
        if not raw:
            return None
        raw = raw.strip().upper()
        mapping = {
            "D": "D", "DEM": "D", "DEMOCRAT": "D", "DEMOCRATIC": "D",
            "R": "R", "REP": "R", "REPUBLICAN": "R",
            "I": "I", "IND": "I", "INDEPENDENT": "I", "NPA": "I", "U": "I",
            "L": "L", "LIB": "L", "LIBERTARIAN": "L",
            "G": "G", "GRN": "G", "GREEN": "G",
        }
        return mapping.get(raw, "O")  # O = other

    def normalize_gender(self, raw: str | None) -> str | None:
        if not raw:
            return None
        raw = raw.strip().upper()
        if raw in ("M", "MALE"):
            return "M"
        if raw in ("F", "FEMALE"):
            return "F"
        return "U"
