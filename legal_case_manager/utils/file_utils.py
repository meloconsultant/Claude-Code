"""File utility functions for the Legal Case Manager."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import FILE_TYPE_MAP


def get_file_type(filepath: str) -> str:
    """Determine document type from file extension."""
    ext = Path(filepath).suffix.lower()
    return FILE_TYPE_MAP.get(ext, f"Unknown ({ext})")


def get_file_metadata(filepath: str) -> dict:
    """Extract basic metadata from a file."""
    path = Path(filepath)
    stat = path.stat()

    return {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "file_type": get_file_type(filepath),
        "size_bytes": stat.st_size,
        "size_human": _human_readable_size(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "absolute_path": str(path.resolve()),
    }


def compute_file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """Compute hash of a file for deduplication."""
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def categorize_file(filepath: str) -> str:
    """Attempt to categorize a file based on name and extension."""
    name = Path(filepath).stem.lower()
    ext = Path(filepath).suffix.lower()

    category_hints = {
        "pleadings": ["complaint", "answer", "pleading", "petition", "motion_to_dismiss"],
        "discovery": ["interrogat", "request_for_prod", "rfp", "rog", "discovery", "subpoena"],
        "witness_statements": ["witness", "statement", "declaration", "affidavit"],
        "depositions": ["depo", "deposition", "transcript"],
        "emails": ["email", "correspondence"],
        "photos": ["photo", "image", "picture", "screenshot"],
        "contracts": ["contract", "agreement", "lease", "mou", "nda"],
        "financial_records": ["invoice", "receipt", "financial", "bank", "tax", "payment"],
        "expert_reports": ["expert", "report", "analysis"],
        "motions": ["motion", "brief", "memorandum", "memo"],
        "orders": ["order", "ruling", "judgment", "decree"],
        "correspondence": ["letter", "memo", "notice"],
        "transcripts": ["transcript", "hearing", "proceeding"],
    }

    if ext in [".eml", ".msg"]:
        return "emails"
    if ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".gif"]:
        return "photos"

    for category, hints in category_hints.items():
        for hint in hints:
            if hint in name:
                return category

    return "other"


def is_supported_file(filepath: str) -> bool:
    """Check if a file type is supported for processing."""
    ext = Path(filepath).suffix.lower()
    return ext in FILE_TYPE_MAP or ext in [".md", ".rtf"]
