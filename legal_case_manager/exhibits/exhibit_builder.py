"""Exhibit Builder - Assigns Bates numbers, tags relevance, builds master list."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.constants import (
    BATES_PREFIX_DEFENDANT,
    BATES_PREFIX_PLAINTIFF,
    COMMON_ISSUES,
    DEFENDANT_BATES_START,
    PLAINTIFF_BATES_START,
    RELEVANCE_TAGS,
)


class Exhibit:
    """Represents a single exhibit in the case."""

    def __init__(
        self,
        exhibit_number: str,
        filename: str,
        file_path: str,
        description: str = "",
        file_type: str = "",
        category: str = "",
    ):
        self.exhibit_number = exhibit_number
        self.filename = filename
        self.file_path = file_path
        self.description = description
        self.file_type = file_type
        self.category = category
        self.relevance: str = "NEUTRAL"
        self.issues: list[str] = []
        self.witnesses: list[str] = []
        self.custodian: str = ""
        self.author: str = ""
        self.date_created: str = ""
        self.keywords: list[str] = []
        self.notes: str = ""
        self.privileged: bool = False
        self.confidential: bool = False

    def to_dict(self) -> dict:
        return {
            "exhibit_number": self.exhibit_number,
            "filename": self.filename,
            "file_path": self.file_path,
            "description": self.description,
            "file_type": self.file_type,
            "category": self.category,
            "relevance": self.relevance,
            "relevance_label": RELEVANCE_TAGS.get(self.relevance, self.relevance),
            "issues": self.issues,
            "witnesses": self.witnesses,
            "custodian": self.custodian,
            "author": self.author,
            "date_created": self.date_created,
            "keywords": self.keywords,
            "notes": self.notes,
            "privileged": self.privileged,
            "confidential": self.confidential,
        }


class ExhibitBuilder:
    """Builds and manages the master exhibits list with Bates numbering."""

    def __init__(self, case_name: str, party: str = "plaintiff"):
        self.case_name = case_name
        self.party = party.lower()
        self.exhibits: list[Exhibit] = []
        self._next_plaintiff_num = PLAINTIFF_BATES_START
        self._next_defendant_num = DEFENDANT_BATES_START

    def _next_bates_number(self, party: Optional[str] = None) -> str:
        """Generate the next Bates number for the given party."""
        p = (party or self.party).lower()
        if p == "plaintiff":
            num = self._next_plaintiff_num
            self._next_plaintiff_num += 1
            return f"{BATES_PREFIX_PLAINTIFF}-{num:06d}"
        else:
            num = self._next_defendant_num
            self._next_defendant_num += 1
            return f"{BATES_PREFIX_DEFENDANT}-{num:06d}"

    def add_exhibit(
        self,
        filename: str,
        file_path: str,
        description: str = "",
        file_type: str = "",
        category: str = "",
        party: Optional[str] = None,
        relevance: str = "NEUTRAL",
        issues: Optional[list[str]] = None,
        witnesses: Optional[list[str]] = None,
        custodian: str = "",
        author: str = "",
        date_created: str = "",
        keywords: Optional[list[str]] = None,
        notes: str = "",
    ) -> Exhibit:
        """Add a new exhibit to the master list."""
        bates = self._next_bates_number(party)

        exhibit = Exhibit(
            exhibit_number=bates,
            filename=filename,
            file_path=file_path,
            description=description or filename,
            file_type=file_type,
            category=category,
        )
        exhibit.relevance = relevance
        exhibit.issues = issues or []
        exhibit.witnesses = witnesses or []
        exhibit.custodian = custodian
        exhibit.author = author
        exhibit.date_created = date_created
        exhibit.keywords = keywords or []
        exhibit.notes = notes
        exhibit.privileged = relevance == "PRIVILEGE"
        exhibit.confidential = relevance == "CONFIDENTIAL"

        self.exhibits.append(exhibit)
        return exhibit

    def add_from_scan_results(
        self, scan_results: list[dict], party: Optional[str] = None
    ) -> list[Exhibit]:
        """Bulk-add exhibits from FileScanner results."""
        added = []
        for file_meta in scan_results:
            exhibit = self.add_exhibit(
                filename=file_meta["filename"],
                file_path=file_meta.get("absolute_path", file_meta.get("relative_path", "")),
                file_type=file_meta.get("file_type", ""),
                category=file_meta.get("category", "other"),
                party=party,
                date_created=file_meta.get("modified", ""),
            )
            added.append(exhibit)
        return added

    def tag_exhibit(
        self,
        exhibit_number: str,
        relevance: Optional[str] = None,
        issues: Optional[list[str]] = None,
        witnesses: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> Optional[Exhibit]:
        """Update tags on an existing exhibit."""
        exhibit = self.get_exhibit(exhibit_number)
        if not exhibit:
            return None

        if relevance:
            exhibit.relevance = relevance
            exhibit.privileged = relevance == "PRIVILEGE"
            exhibit.confidential = relevance == "CONFIDENTIAL"
        if issues:
            exhibit.issues = list(set(exhibit.issues + issues))
        if witnesses:
            exhibit.witnesses = list(set(exhibit.witnesses + witnesses))
        if notes:
            exhibit.notes = notes
        return exhibit

    def get_exhibit(self, exhibit_number: str) -> Optional[Exhibit]:
        """Look up an exhibit by its Bates number."""
        for ex in self.exhibits:
            if ex.exhibit_number == exhibit_number:
                return ex
        return None

    def filter_exhibits(
        self,
        relevance: Optional[str] = None,
        issue: Optional[str] = None,
        category: Optional[str] = None,
        witness: Optional[str] = None,
    ) -> list[Exhibit]:
        """Filter exhibits by criteria."""
        results = self.exhibits
        if relevance:
            results = [e for e in results if e.relevance == relevance]
        if issue:
            results = [e for e in results if issue in e.issues]
        if category:
            results = [e for e in results if e.category == category]
        if witness:
            results = [
                e for e in results if witness.lower() in [w.lower() for w in e.witnesses]
            ]
        return results

    def get_hot_documents(self) -> dict[str, list[Exhibit]]:
        """Get hot documents grouped by type."""
        return {
            "hot_good": self.filter_exhibits(relevance="HOT_GOOD"),
            "hot_bad": self.filter_exhibits(relevance="HOT_BAD"),
            "privileged": self.filter_exhibits(relevance="PRIVILEGE"),
            "confidential": self.filter_exhibits(relevance="CONFIDENTIAL"),
        }

    def format_master_table(self) -> str:
        """Format the exhibits list as a markdown table."""
        lines = [
            f"# Master Exhibits List - {self.case_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total Exhibits: {len(self.exhibits)}",
            "",
            "| Exhibit # | File | Description | Relevance | Issue(s) | Witness(es) | Notes |",
            "|-----------|------|-------------|-----------|----------|-------------|-------|",
        ]

        for ex in self.exhibits:
            issues_str = ", ".join(ex.issues) if ex.issues else "-"
            witnesses_str = ", ".join(ex.witnesses) if ex.witnesses else "-"
            relevance_label = RELEVANCE_TAGS.get(ex.relevance, ex.relevance)
            lines.append(
                f"| {ex.exhibit_number} | {ex.filename} | "
                f"{ex.description[:50]} | {relevance_label} | "
                f"{issues_str} | {witnesses_str} | {ex.notes[:30] if ex.notes else '-'} |"
            )

        return "\n".join(lines)

    def export_csv(self, output_path: str) -> str:
        """Export the master exhibits list to CSV."""
        fieldnames = [
            "exhibit_number", "filename", "file_path", "description",
            "file_type", "category", "relevance", "issues", "witnesses",
            "custodian", "author", "date_created", "keywords", "notes",
            "privileged", "confidential",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ex in self.exhibits:
                row = ex.to_dict()
                row["issues"] = "; ".join(row["issues"])
                row["witnesses"] = "; ".join(row["witnesses"])
                row["keywords"] = "; ".join(row["keywords"])
                del row["relevance_label"]
                writer.writerow(row)

        return output_path

    def export_json(self, output_path: str) -> str:
        """Export the master exhibits list to JSON."""
        data = {
            "case_name": self.case_name,
            "generated": datetime.now().isoformat(),
            "total_exhibits": len(self.exhibits),
            "exhibits": [ex.to_dict() for ex in self.exhibits],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return output_path

    def get_summary(self) -> dict:
        """Return a summary of the exhibits list."""
        hot = self.get_hot_documents()
        return {
            "case_name": self.case_name,
            "total_exhibits": len(self.exhibits),
            "by_relevance": {
                tag: len(self.filter_exhibits(relevance=tag))
                for tag in RELEVANCE_TAGS
            },
            "by_category": self._count_by("category"),
            "hot_good_count": len(hot["hot_good"]),
            "hot_bad_count": len(hot["hot_bad"]),
            "privileged_count": len(hot["privileged"]),
            "issues_covered": self._unique_issues(),
            "witnesses_referenced": self._unique_witnesses(),
        }

    def _count_by(self, field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ex in self.exhibits:
            val = getattr(ex, field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts

    def _unique_issues(self) -> list[str]:
        issues = set()
        for ex in self.exhibits:
            issues.update(ex.issues)
        return sorted(issues)

    def _unique_witnesses(self) -> list[str]:
        witnesses = set()
        for ex in self.exhibits:
            witnesses.update(ex.witnesses)
        return sorted(witnesses)
