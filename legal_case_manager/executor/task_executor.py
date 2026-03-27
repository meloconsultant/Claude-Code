"""Task Executor - Proposes and executes paralegal tasks."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..exhibits.exhibit_builder import ExhibitBuilder
from ..scanners.file_scanner import FileScanner
from ..tracker.case_tracker import CaseTracker


class SearchResult:
    """Represents a keyword search hit across case files."""

    def __init__(self, filepath: str, line_number: int, line_content: str, keyword: str):
        self.filepath = filepath
        self.line_number = line_number
        self.line_content = line_content.strip()
        self.keyword = keyword

    def to_dict(self) -> dict:
        return {
            "file": self.filepath,
            "line": self.line_number,
            "content": self.line_content,
            "keyword": self.keyword,
        }


class TaskExecutor:
    """Proposes next steps and executes case management tasks."""

    def __init__(
        self,
        scanner: FileScanner,
        exhibit_builder: ExhibitBuilder,
        case_tracker: CaseTracker,
    ):
        self.scanner = scanner
        self.exhibit_builder = exhibit_builder
        self.tracker = case_tracker

    def propose_next_steps(self) -> list[dict]:
        """Analyze current case state and propose 3-5 actionable next steps."""
        proposals = []
        phase = self.tracker.current_phase
        summary = self.scanner.get_summary() if self.scanner.files else None
        exhibit_summary = self.exhibit_builder.get_summary()

        # Phase-specific proposals
        if phase == "intake":
            proposals.append({
                "action": "scan_files",
                "description": "Scan and inventory all case files",
                "priority": "high",
                "command": "scan",
            })
            proposals.append({
                "action": "build_exhibits",
                "description": "Build master exhibits list from scanned files",
                "priority": "high",
                "command": "build_exhibits",
            })

        if phase in ("intake", "pleadings"):
            proposals.append({
                "action": "identify_themes",
                "description": "Identify case themes and tag exhibits by issue",
                "priority": "high",
                "command": "tag_issues",
            })

        if phase == "discovery":
            proposals.append({
                "action": "keyword_search",
                "description": "Run keyword search across all text files for key terms",
                "priority": "high",
                "command": "search",
            })
            proposals.append({
                "action": "privilege_review",
                "description": "Review documents for privilege and mark for redaction",
                "priority": "critical",
                "command": "privilege_review",
            })
            proposals.append({
                "action": "draft_privilege_log",
                "description": "Draft privilege log from tagged documents",
                "priority": "high",
                "command": "privilege_log",
            })

        if phase == "motions":
            proposals.append({
                "action": "compile_evidence",
                "description": "Compile hot documents for motion support",
                "priority": "high",
                "command": "hot_docs",
            })

        if phase == "trial_prep":
            proposals.append({
                "action": "prep_witness_binders",
                "description": "Prepare witness binders with linked exhibits",
                "priority": "critical",
                "command": "witness_binders",
            })
            proposals.append({
                "action": "trial_exhibit_list",
                "description": "Generate trial exhibit list for court filing",
                "priority": "critical",
                "command": "trial_exhibits",
            })

        # Universal proposals
        overdue = self.tracker.get_overdue_deadlines()
        if overdue:
            proposals.append({
                "action": "address_overdue",
                "description": f"Address {len(overdue)} overdue deadline(s)",
                "priority": "critical",
                "command": "deadlines",
            })

        if self.tracker.gaps:
            proposals.append({
                "action": "resolve_gaps",
                "description": f"Resolve {len(self.tracker.gaps)} identified gap(s)",
                "priority": "high",
                "command": "gaps",
            })

        if summary and summary.get("duplicates_found", 0) > 0:
            proposals.append({
                "action": "deduplicate",
                "description": f"Review {summary['duplicates_found']} duplicate file(s)",
                "priority": "normal",
                "command": "dedup",
            })

        # Always suggest export
        if exhibit_summary["total_exhibits"] > 0:
            proposals.append({
                "action": "export",
                "description": "Export exhibits list to CSV/JSON",
                "priority": "normal",
                "command": "export",
            })

        # Sort by priority and return top 5
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        proposals.sort(key=lambda p: priority_order.get(p["priority"], 99))
        return proposals[:5]

    def keyword_search(
        self, keywords: list[str], file_extensions: Optional[list[str]] = None
    ) -> list[SearchResult]:
        """Search text files in the case directory for keywords."""
        results = []
        extensions = file_extensions or [".txt", ".eml", ".csv", ".md", ".html", ".json"]
        case_dir = self.scanner.case_directory

        for filepath in case_dir.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in extensions:
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for keyword in keywords:
                            if re.search(
                                re.escape(keyword), line, re.IGNORECASE
                            ):
                                results.append(
                                    SearchResult(
                                        filepath=str(
                                            filepath.relative_to(case_dir)
                                        ),
                                        line_number=line_num,
                                        line_content=line,
                                        keyword=keyword,
                                    )
                                )
            except (PermissionError, OSError):
                continue

        return results

    def generate_privilege_log(self) -> str:
        """Generate a privilege log from tagged exhibits."""
        privileged = self.exhibit_builder.filter_exhibits(relevance="PRIVILEGE")
        if not privileged:
            return "No privileged documents found. Tag exhibits with PRIVILEGE relevance first."

        lines = [
            "# Privilege Log",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total Privileged Documents: {len(privileged)}",
            "",
            "| Bates # | Document | Date | Author | Custodian | Privilege Type | Description |",
            "|---------|----------|------|--------|-----------|---------------|-------------|",
        ]

        for ex in privileged:
            lines.append(
                f"| {ex.exhibit_number} | {ex.filename} | "
                f"{ex.date_created[:10] if ex.date_created else 'N/A'} | "
                f"{ex.author or 'N/A'} | {ex.custodian or 'N/A'} | "
                f"Attorney-Client | {ex.description[:40]} |"
            )

        return "\n".join(lines)

    def generate_witness_binder(self, witness_name: str) -> str:
        """Generate a witness binder listing all exhibits linked to a witness."""
        exhibits = self.exhibit_builder.filter_exhibits(witness=witness_name)
        if not exhibits:
            return f"No exhibits linked to witness '{witness_name}'."

        lines = [
            f"# Witness Binder: {witness_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total Exhibits: {len(exhibits)}",
            "",
            "| Exhibit # | Document | Relevance | Issues | Notes |",
            "|-----------|----------|-----------|--------|-------|",
        ]

        for ex in exhibits:
            issues = ", ".join(ex.issues) if ex.issues else "-"
            lines.append(
                f"| {ex.exhibit_number} | {ex.filename} | "
                f"{ex.relevance} | {issues} | {ex.notes[:30] if ex.notes else '-'} |"
            )

        return "\n".join(lines)

    def generate_trial_exhibit_list(self) -> str:
        """Generate a trial exhibit list suitable for court filing."""
        exhibits = self.exhibit_builder.exhibits
        if not exhibits:
            return "No exhibits in the master list."

        lines = [
            f"# Trial Exhibit List - {self.exhibit_builder.case_name}",
            f"Filed: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "| No. | Exhibit # | Description | Offered By | Status |",
            "|-----|-----------|-------------|------------|--------|",
        ]

        for i, ex in enumerate(exhibits, 1):
            if ex.privileged:
                continue
            party = "Plaintiff" if ex.exhibit_number.startswith("PLTF") else "Defendant"
            lines.append(
                f"| {i} | {ex.exhibit_number} | "
                f"{ex.description[:60]} | {party} | Pending |"
            )

        return "\n".join(lines)

    def format_search_results(self, results: list[SearchResult]) -> str:
        """Format keyword search results as a readable report."""
        if not results:
            return "No matches found."

        by_keyword: dict[str, list[SearchResult]] = {}
        for r in results:
            by_keyword.setdefault(r.keyword, []).append(r)

        lines = [
            f"# Keyword Search Results",
            f"Total Hits: {len(results)}",
            "",
        ]

        for keyword, hits in by_keyword.items():
            lines.append(f"## '{keyword}' - {len(hits)} hit(s)")
            for h in hits[:20]:  # Limit display
                lines.append(
                    f"  - **{h.filepath}** (line {h.line_number}): "
                    f"`{h.line_content[:80]}`"
                )
            if len(hits) > 20:
                lines.append(f"  ... and {len(hits) - 20} more")
            lines.append("")

        return "\n".join(lines)
