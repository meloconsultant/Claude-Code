"""CLI entry point for the Legal Case Manager Agent."""

import argparse
import sys

from .agent import LegalCaseAgent


def main():
    parser = argparse.ArgumentParser(
        description="Legal Case Manager Agent - Senior paralegal + litigator hybrid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --case "Smith v. Jones" --dir ./case_files
  %(prog)s --case "Smith v. Jones" --dir ./case_files --command status
  %(prog)s --case "Smith v. Jones" --dir ./case_files --command search --keywords fraud misrep
  %(prog)s --case "Smith v. Jones" --dir ./case_files --command export_csv
        """,
    )

    parser.add_argument(
        "--case", required=True, help="Case name (e.g., 'Smith v. Jones')"
    )
    parser.add_argument(
        "--dir", required=True, help="Path to case files directory"
    )
    parser.add_argument(
        "--number", default="", help="Case number (optional)"
    )
    parser.add_argument(
        "--command",
        default="init",
        help="Command to execute (default: init). Use 'help' for full list.",
    )
    parser.add_argument(
        "--phase", default="", help="Case phase for set_phase command"
    )
    parser.add_argument(
        "--keywords", nargs="*", help="Keywords for search command"
    )
    parser.add_argument(
        "--exhibit", default="", help="Exhibit number for tag command"
    )
    parser.add_argument(
        "--relevance", default="", help="Relevance tag for tag command"
    )
    parser.add_argument(
        "--issues", nargs="*", help="Issues for tag command"
    )
    parser.add_argument(
        "--witnesses", nargs="*", help="Witnesses for tag command"
    )
    parser.add_argument(
        "--witness-name", default="", help="Witness name for witness_binder"
    )
    parser.add_argument(
        "--output", default="", help="Output path for export commands"
    )
    parser.add_argument(
        "--deadline-name", default="", help="Deadline name"
    )
    parser.add_argument(
        "--due-date", default="", help="Due date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--task-desc", default="", help="Task description"
    )
    parser.add_argument(
        "--priority", default="normal", help="Task priority"
    )

    args = parser.parse_args()

    agent = LegalCaseAgent(
        case_name=args.case,
        case_directory=args.dir,
        case_number=args.number,
    )

    if args.command == "init":
        print(agent.initialize())
    else:
        kwargs = {}
        if args.keywords:
            kwargs["keywords"] = args.keywords
        if args.phase:
            kwargs["phase"] = args.phase
        if args.exhibit:
            kwargs["exhibit_number"] = args.exhibit
        if args.relevance:
            kwargs["relevance"] = args.relevance
        if args.issues:
            kwargs["issues"] = args.issues
        if args.witnesses:
            kwargs["witnesses"] = args.witnesses
        if args.witness_name:
            kwargs["witness_name"] = args.witness_name
        if args.output:
            kwargs["output_path"] = args.output
        if args.deadline_name:
            kwargs["name"] = args.deadline_name
        if args.due_date:
            kwargs["due_date"] = args.due_date
        if args.task_desc:
            kwargs["description"] = args.task_desc
        if args.priority != "normal":
            kwargs["priority"] = args.priority

        print(agent.handle_command(args.command, **kwargs))


if __name__ == "__main__":
    main()
