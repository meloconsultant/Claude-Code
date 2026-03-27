"""File Scanner - Inventories all case files and detects duplicates."""

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from ..utils.constants import DOC_CATEGORIES
from ..utils.file_utils import (
    categorize_file,
    compute_file_hash,
    get_file_metadata,
    is_supported_file,
)


class FileScanner:
    """Scans directories for case files, inventories them, and flags issues."""

    def __init__(self, case_directory: str):
        self.case_directory = Path(case_directory).resolve()
        self.files: list[dict] = []
        self.duplicates: list[tuple[str, str]] = []
        self.corrupted: list[str] = []
        self._hash_map: dict[str, list[str]] = defaultdict(list)

    def scan(self, recursive: bool = True) -> list[dict]:
        """Scan the case directory and inventory all files.

        Returns a list of file metadata dicts grouped by category.
        """
        self.files = []
        self._hash_map.clear()

        if not self.case_directory.exists():
            raise FileNotFoundError(
                f"Case directory not found: {self.case_directory}"
            )

        pattern = "**/*" if recursive else "*"
        for filepath in sorted(self.case_directory.glob(pattern)):
            if not filepath.is_file():
                continue
            if filepath.name.startswith("."):
                continue

            try:
                metadata = get_file_metadata(str(filepath))
                metadata["category"] = categorize_file(str(filepath))
                metadata["supported"] = is_supported_file(str(filepath))
                metadata["relative_path"] = str(
                    filepath.relative_to(self.case_directory)
                )

                file_hash = compute_file_hash(str(filepath))
                metadata["hash"] = file_hash
                self._hash_map[file_hash].append(str(filepath))

                self.files.append(metadata)

            except (PermissionError, OSError) as e:
                self.corrupted.append(str(filepath))

        self._detect_duplicates()
        return self.files

    def _detect_duplicates(self) -> None:
        """Identify duplicate files by content hash."""
        self.duplicates = []
        for file_hash, paths in self._hash_map.items():
            if len(paths) > 1:
                for i in range(len(paths)):
                    for j in range(i + 1, len(paths)):
                        self.duplicates.append((paths[i], paths[j]))

    def get_inventory_by_category(self) -> dict[str, list[dict]]:
        """Group scanned files by document category."""
        grouped: dict[str, list[dict]] = defaultdict(list)
        for f in self.files:
            grouped[f["category"]].append(f)
        return dict(grouped)

    def get_summary(self) -> dict:
        """Return a summary of the scan results."""
        categories = self.get_inventory_by_category()
        return {
            "total_files": len(self.files),
            "categories": {k: len(v) for k, v in categories.items()},
            "duplicates_found": len(self.duplicates),
            "corrupted_files": len(self.corrupted),
            "supported_files": sum(1 for f in self.files if f["supported"]),
            "unsupported_files": sum(
                1 for f in self.files if not f["supported"]
            ),
        }

    def format_inventory_table(self) -> str:
        """Format the inventory as a markdown table."""
        if not self.files:
            return "No files found. Run scan() first."

        lines = [
            "| # | Filename | Type | Category | Size | Modified | Path |",
            "|---|----------|------|----------|------|----------|------|",
        ]

        for i, f in enumerate(self.files, 1):
            lines.append(
                f"| {i} | {f['filename']} | {f['file_type']} | "
                f"{f['category']} | {f['size_human']} | "
                f"{f['modified'][:10]} | {f['relative_path']} |"
            )

        if self.duplicates:
            lines.append("\n### Duplicate Files Detected")
            for dup_a, dup_b in self.duplicates:
                lines.append(f"- `{Path(dup_a).name}` == `{Path(dup_b).name}`")

        if self.corrupted:
            lines.append("\n### Corrupted / Inaccessible Files")
            for c in self.corrupted:
                lines.append(f"- `{c}`")

        return "\n".join(lines)

    def search_files(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> list[dict]:
        """Search scanned files by keyword, category, or extension."""
        results = self.files

        if keyword:
            keyword_lower = keyword.lower()
            results = [
                f
                for f in results
                if keyword_lower in f["filename"].lower()
                or keyword_lower in f.get("relative_path", "").lower()
            ]

        if category:
            results = [f for f in results if f["category"] == category]

        if extension:
            ext = extension if extension.startswith(".") else f".{extension}"
            results = [f for f in results if f["extension"] == ext.lower()]

        return results
