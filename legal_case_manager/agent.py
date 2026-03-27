"""Legal Case Manager Agent - Main orchestrator.

Acts as senior paralegal + litigator hybrid. Scans files, builds exhibits,
tracks case status, flags next steps, and executes tasks.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from .exhibits.exhibit_builder import ExhibitBuilder
from .executor.task_executor import TaskExecutor
from .scanners.file_scanner import FileScanner
from .tracker.case_tracker import CaseTracker
from .utils.constants import CASE_PHASE_LABELS, COMMON_ISSUES, RELEVANCE_TAGS


class LegalCaseAgent:
    """Main agent that orchestrates all legal case management operations."""

    def __init__(self, case_name: str, case_directory: str, case_number: str = ""):
        self.case_name = case_name
        self.case_directory = case_directory
        self.case_number = case_number

        # Initialize components
        self.scanner = FileScanner(case_directory)
        self.exhibits = ExhibitBuilder(case_name)
        self.tracker = CaseTracker(case_name, case_number)
        self.executor = TaskExecutor(self.scanner, self.exhibits, self.tracker)

        self._initialized = False

    def initialize(self) -> str:
        """Run initial scan and build exhibits list."""
        output = []

        # Step 1: Scan files
        output.append("## Step 1: Scanning Case Files")
        try:
            files = self.scanner.scan()
            summary = self.scanner.get_summary()
            output.append(
                f"Scanned **{summary['total_files']}** files across "
                f"**{len(summary['categories'])}** categories."
            )
            if summary["duplicates_found"] > 0:
                output.append(
                    f"**{summary['duplicates_found']}** duplicate(s) detected."
                )
            if summary["corrupted_files"] > 0:
                output.append(
                    f"**{summary['corrupted_files']}** corrupted/inaccessible file(s)."
                )
            output.append("")
            output.append(self.scanner.format_inventory_table())
        except FileNotFoundError as e:
            output.append(f"Error: {e}")
            return "\n".join(output)

        # Step 2: Build exhibits list
        output.append("\n## Step 2: Building Exhibits List")
        added = self.exhibits.add_from_scan_results(files)
        output.append(
            f"Created **{len(added)}** exhibit entries with Bates numbers "
            f"(PLTF-000001 through PLTF-{len(added):06d})."
        )
        output.append("")
        output.append(self.exhibits.format_master_table())

        # Step 3: Map case status
        output.append("\n## Step 3: Case Status")
        progress = self.tracker.get_phase_progress()
        output.append(
            f"Case at **{progress['current_phase_label']}** phase. "
            f"Next: tag exhibits by relevance and issue."
        )

        # Step 4: Propose next steps
        output.append("\n## Step 4: Recommended Next Steps")
        proposals = self.executor.propose_next_steps()
        for i, p in enumerate(proposals, 1):
            output.append(
                f"{i}. **[{p['priority'].upper()}]** {p['description']}"
            )

        output.append("\nConfirm to proceed with any action, or ask for details.")

        self._initialized = True
        return "\n".join(output)

    def handle_command(self, command: str, **kwargs) -> str:
        """Route a command to the appropriate handler."""
        commands = {
            "scan": self._cmd_scan,
            "build_exhibits": self._cmd_build_exhibits,
            "status": self._cmd_status,
            "next": self._cmd_next_steps,
            "search": self._cmd_search,
            "tag": self._cmd_tag,
            "privilege_log": self._cmd_privilege_log,
            "witness_binder": self._cmd_witness_binder,
            "trial_exhibits": self._cmd_trial_exhibits,
            "hot_docs": self._cmd_hot_docs,
            "export_csv": self._cmd_export_csv,
            "export_json": self._cmd_export_json,
            "set_phase": self._cmd_set_phase,
            "advance_phase": self._cmd_advance_phase,
            "add_deadline": self._cmd_add_deadline,
            "add_task": self._cmd_add_task,
            "help": self._cmd_help,
        }

        handler = commands.get(command)
        if not handler:
            return (
                f"Unknown command: '{command}'. "
                f"Available: {', '.join(sorted(commands.keys()))}"
            )

        return handler(**kwargs)

    def _cmd_scan(self, **kwargs) -> str:
        self.scanner.scan()
        return self.scanner.format_inventory_table()

    def _cmd_build_exhibits(self, **kwargs) -> str:
        if not self.scanner.files:
            self.scanner.scan()
        added = self.exhibits.add_from_scan_results(self.scanner.files)
        return (
            f"Added {len(added)} exhibits.\n\n"
            + self.exhibits.format_master_table()
        )

    def _cmd_status(self, **kwargs) -> str:
        return self.tracker.get_status_report()

    def _cmd_next_steps(self, **kwargs) -> str:
        proposals = self.executor.propose_next_steps()
        if not proposals:
            return "No specific actions recommended at this time."
        lines = ["## Recommended Next Steps"]
        for i, p in enumerate(proposals, 1):
            lines.append(
                f"{i}. **[{p['priority'].upper()}]** {p['description']} "
                f"(command: `{p['command']}`)"
            )
        return "\n".join(lines)

    def _cmd_search(self, keywords: Optional[list[str]] = None, **kwargs) -> str:
        if not keywords:
            return "Provide keywords to search. Example: search keywords=['fraud', 'misrep']"
        results = self.executor.keyword_search(keywords)
        return self.executor.format_search_results(results)

    def _cmd_tag(
        self,
        exhibit_number: str = "",
        relevance: Optional[str] = None,
        issues: Optional[list[str]] = None,
        witnesses: Optional[list[str]] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> str:
        if not exhibit_number:
            return (
                f"Provide exhibit_number. "
                f"Relevance tags: {', '.join(RELEVANCE_TAGS.keys())}. "
                f"Issues: {', '.join(COMMON_ISSUES[:5])}..."
            )
        result = self.exhibits.tag_exhibit(
            exhibit_number, relevance, issues, witnesses, notes
        )
        if not result:
            return f"Exhibit '{exhibit_number}' not found."
        return f"Updated {exhibit_number}: relevance={result.relevance}, issues={result.issues}"

    def _cmd_privilege_log(self, **kwargs) -> str:
        return self.executor.generate_privilege_log()

    def _cmd_witness_binder(self, witness_name: str = "", **kwargs) -> str:
        if not witness_name:
            return "Provide witness_name parameter."
        return self.executor.generate_witness_binder(witness_name)

    def _cmd_trial_exhibits(self, **kwargs) -> str:
        return self.executor.generate_trial_exhibit_list()

    def _cmd_hot_docs(self, **kwargs) -> str:
        hot = self.exhibits.get_hot_documents()
        lines = ["## Hot Documents Summary"]
        for label, docs in hot.items():
            lines.append(f"\n### {label.replace('_', ' ').title()} ({len(docs)})")
            for d in docs:
                lines.append(f"- {d.exhibit_number}: {d.filename} - {d.description[:50]}")
            if not docs:
                lines.append("- None tagged yet")
        return "\n".join(lines)

    def _cmd_export_csv(self, output_path: str = "", **kwargs) -> str:
        path = output_path or str(
            Path(self.case_directory) / "exhibits-master.csv"
        )
        result = self.exhibits.export_csv(path)
        return f"Exhibits list exported to: {result}"

    def _cmd_export_json(self, output_path: str = "", **kwargs) -> str:
        path = output_path or str(
            Path(self.case_directory) / "exhibits-master.json"
        )
        result = self.exhibits.export_json(path)
        return f"Exhibits list exported to: {result}"

    def _cmd_set_phase(self, phase: str = "", **kwargs) -> str:
        if not phase:
            return (
                f"Current: {CASE_PHASE_LABELS[self.tracker.current_phase]}. "
                f"Available: {', '.join(CASE_PHASE_LABELS.values())}"
            )
        return self.tracker.set_phase(phase)

    def _cmd_advance_phase(self, **kwargs) -> str:
        return self.tracker.advance_phase()

    def _cmd_add_deadline(
        self, name: str = "", due_date: str = "", description: str = "", **kwargs
    ) -> str:
        if not name or not due_date:
            return "Provide name and due_date (YYYY-MM-DD) parameters."
        d = self.tracker.add_deadline(name, due_date, description=description)
        return f"Deadline added: {d.name} due {d.due_date}"

    def _cmd_add_task(
        self, description: str = "", priority: str = "normal", **kwargs
    ) -> str:
        if not description:
            return "Provide description parameter."
        t = self.tracker.add_task(description, priority=priority)
        return f"Task {t.task_id} created: {t.description} ({t.priority})"

    def _cmd_help(self, **kwargs) -> str:
        return """# Legal Case Manager - Commands

## File Operations
- **scan** - Scan and inventory all case files
- **build_exhibits** - Build master exhibits list from scanned files
- **search** keywords=['term1','term2'] - Keyword search across text files

## Exhibits Management
- **tag** exhibit_number=PLTF-000001 relevance=HOT_GOOD issues=['fraud'] - Tag an exhibit
- **hot_docs** - View hot documents summary
- **privilege_log** - Generate privilege log
- **witness_binder** witness_name='Smith' - Generate witness binder
- **trial_exhibits** - Generate trial exhibit list

## Case Tracking
- **status** - Full case status report
- **next** - Get recommended next steps
- **set_phase** phase=discovery - Set current case phase
- **advance_phase** - Move to next phase
- **add_deadline** name='Discovery Cutoff' due_date='2026-06-01' - Add deadline
- **add_task** description='Review ESI' priority=high - Add task

## Export
- **export_csv** - Export exhibits to CSV
- **export_json** - Export exhibits to JSON

## Relevance Tags
HOT_GOOD, HOT_BAD, NEUTRAL, PRIVILEGE, CONFIDENTIAL, WORK_PRODUCT

## Case Phases
intake → pleadings → discovery → motions → trial_prep → trial → post_trial → appeal
"""
