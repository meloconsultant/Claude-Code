"""Case Status Tracker - Maps case timeline, phases, deadlines, and gaps."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..utils.constants import CASE_PHASE_LABELS, CASE_PHASES


class Deadline:
    """Represents a case deadline."""

    def __init__(
        self,
        name: str,
        due_date: str,
        phase: str,
        description: str = "",
        completed: bool = False,
    ):
        self.name = name
        self.due_date = due_date
        self.phase = phase
        self.description = description
        self.completed = completed

    @property
    def is_overdue(self) -> bool:
        try:
            due = datetime.fromisoformat(self.due_date)
            return not self.completed and due < datetime.now()
        except ValueError:
            return False

    @property
    def days_remaining(self) -> Optional[int]:
        try:
            due = datetime.fromisoformat(self.due_date)
            delta = due - datetime.now()
            return delta.days
        except ValueError:
            return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "due_date": self.due_date,
            "phase": self.phase,
            "description": self.description,
            "completed": self.completed,
            "is_overdue": self.is_overdue,
            "days_remaining": self.days_remaining,
        }


class CaseTask:
    """Represents a tracked task in the case."""

    def __init__(
        self,
        task_id: str,
        description: str,
        phase: str,
        status: str = "pending",
        assigned_to: str = "",
        priority: str = "normal",
    ):
        self.task_id = task_id
        self.description = description
        self.phase = phase
        self.status = status  # pending, in_progress, completed, blocked
        self.assigned_to = assigned_to
        self.priority = priority  # low, normal, high, critical
        self.created_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.notes: str = ""

    def complete(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "phase": self.phase,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "notes": self.notes,
        }


class CaseTracker:
    """Tracks case phase, deadlines, completed work, and gaps."""

    def __init__(self, case_name: str, case_number: str = ""):
        self.case_name = case_name
        self.case_number = case_number
        self.current_phase: str = "intake"
        self.deadlines: list[Deadline] = []
        self.tasks: list[CaseTask] = []
        self.completed_milestones: list[str] = []
        self.gaps: list[str] = []
        self.notes: list[str] = []
        self._task_counter = 0

    def set_phase(self, phase: str) -> str:
        """Set the current case phase."""
        if phase not in CASE_PHASES:
            return f"Invalid phase '{phase}'. Valid: {', '.join(CASE_PHASES)}"
        self.current_phase = phase
        return f"Case phase set to: {CASE_PHASE_LABELS[phase]}"

    def advance_phase(self) -> str:
        """Move to the next case phase."""
        idx = CASE_PHASES.index(self.current_phase)
        if idx >= len(CASE_PHASES) - 1:
            return "Already at final phase (Appeal)."
        self.current_phase = CASE_PHASES[idx + 1]
        return f"Advanced to: {CASE_PHASE_LABELS[self.current_phase]}"

    def get_phase_progress(self) -> dict:
        """Get progress through case phases."""
        current_idx = CASE_PHASES.index(self.current_phase)
        total = len(CASE_PHASES)
        return {
            "current_phase": self.current_phase,
            "current_phase_label": CASE_PHASE_LABELS[self.current_phase],
            "phase_number": current_idx + 1,
            "total_phases": total,
            "percent_complete": round((current_idx / (total - 1)) * 100),
            "phases_completed": CASE_PHASES[:current_idx],
            "phases_remaining": CASE_PHASES[current_idx + 1:],
        }

    def add_deadline(
        self,
        name: str,
        due_date: str,
        phase: Optional[str] = None,
        description: str = "",
    ) -> Deadline:
        """Add a deadline to the case."""
        deadline = Deadline(
            name=name,
            due_date=due_date,
            phase=phase or self.current_phase,
            description=description,
        )
        self.deadlines.append(deadline)
        return deadline

    def complete_deadline(self, name: str) -> Optional[Deadline]:
        """Mark a deadline as completed."""
        for d in self.deadlines:
            if d.name == name:
                d.completed = True
                return d
        return None

    def get_upcoming_deadlines(self, days: int = 30) -> list[Deadline]:
        """Get deadlines within the next N days."""
        cutoff = datetime.now() + timedelta(days=days)
        upcoming = []
        for d in self.deadlines:
            if d.completed:
                continue
            try:
                due = datetime.fromisoformat(d.due_date)
                if due <= cutoff:
                    upcoming.append(d)
            except ValueError:
                continue
        return sorted(upcoming, key=lambda d: d.due_date)

    def get_overdue_deadlines(self) -> list[Deadline]:
        """Get all overdue deadlines."""
        return [d for d in self.deadlines if d.is_overdue]

    def add_task(
        self,
        description: str,
        phase: Optional[str] = None,
        priority: str = "normal",
        assigned_to: str = "",
    ) -> CaseTask:
        """Add a new task to the case."""
        self._task_counter += 1
        task = CaseTask(
            task_id=f"TASK-{self._task_counter:04d}",
            description=description,
            phase=phase or self.current_phase,
            priority=priority,
            assigned_to=assigned_to,
        )
        self.tasks.append(task)
        return task

    def complete_task(self, task_id: str) -> Optional[CaseTask]:
        """Mark a task as completed."""
        for t in self.tasks:
            if t.task_id == task_id:
                t.complete()
                return t
        return None

    def add_gap(self, description: str) -> None:
        """Flag a gap or missing item in the case."""
        self.gaps.append(description)

    def add_milestone(self, description: str) -> None:
        """Record a completed milestone."""
        self.completed_milestones.append(description)

    def get_status_report(self) -> str:
        """Generate a full case status report."""
        progress = self.get_phase_progress()
        overdue = self.get_overdue_deadlines()
        upcoming = self.get_upcoming_deadlines(days=30)
        pending_tasks = [t for t in self.tasks if t.status in ("pending", "in_progress")]
        completed_tasks = [t for t in self.tasks if t.status == "completed"]

        lines = [
            f"# Case Status Report: {self.case_name}",
            f"**Case Number:** {self.case_number or 'Not assigned'}",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Current Phase",
            f"**{progress['current_phase_label']}** "
            f"(Phase {progress['phase_number']}/{progress['total_phases']}, "
            f"{progress['percent_complete']}% through lifecycle)",
            "",
        ]

        if self.completed_milestones:
            lines.append("## Completed Milestones")
            for m in self.completed_milestones:
                lines.append(f"- [x] {m}")
            lines.append("")

        if overdue:
            lines.append("## OVERDUE DEADLINES")
            for d in overdue:
                lines.append(
                    f"- **{d.name}** - Due: {d.due_date} "
                    f"({abs(d.days_remaining or 0)} days overdue) - {d.description}"
                )
            lines.append("")

        if upcoming:
            lines.append("## Upcoming Deadlines (30 days)")
            for d in upcoming:
                lines.append(
                    f"- {d.name} - Due: {d.due_date} "
                    f"({d.days_remaining} days) - {d.description}"
                )
            lines.append("")

        if pending_tasks:
            lines.append("## Pending Tasks")
            for t in pending_tasks:
                priority_marker = "!" if t.priority in ("high", "critical") else "-"
                lines.append(
                    f"{priority_marker} [{t.task_id}] {t.description} "
                    f"({t.priority}, {t.status})"
                )
            lines.append("")

        if self.gaps:
            lines.append("## Gaps & Missing Items")
            for g in self.gaps:
                lines.append(f"- {g}")
            lines.append("")

        lines.append(
            f"**Summary:** {len(completed_tasks)} tasks done, "
            f"{len(pending_tasks)} pending, "
            f"{len(overdue)} overdue deadlines, "
            f"{len(self.gaps)} gaps flagged."
        )

        return "\n".join(lines)

    def export_json(self, output_path: str) -> str:
        """Export case status to JSON."""
        data = {
            "case_name": self.case_name,
            "case_number": self.case_number,
            "current_phase": self.current_phase,
            "phase_progress": self.get_phase_progress(),
            "deadlines": [d.to_dict() for d in self.deadlines],
            "tasks": [t.to_dict() for t in self.tasks],
            "completed_milestones": self.completed_milestones,
            "gaps": self.gaps,
            "generated": datetime.now().isoformat(),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return output_path
