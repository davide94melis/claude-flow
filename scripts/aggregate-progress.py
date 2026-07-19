"""[DEPRECATED] Aggregate PROGRESS.md files across branches ("highest progress wins").

DEPRECATED (SDLC feedback round #4): the progress model is CENTRALIZED — PROGRESS.md and
PROGRESS.xlsx live on 'main' of the specs/profiles repo and are read directly via
`git show origin/main:...` by sdlc-progress-report. Cross-branch aggregation contradicts
that model and is disabled. Kept for reference only; running it exits non-zero.
"""
import os
import re
import sys
from pathlib import Path


def parse_progress(content: str) -> tuple[str, dict, str]:
    """Parse a PROGRESS.md, returning (header_block, tasks_dict, footer_block).

    tasks_dict: {task_id: (progress_int, status_priority_int, full_row_text)}
    """
    lines = content.split("\n")
    tasks = {}
    header_lines = []
    footer_lines = []
    in_state_table = False
    state_table_done = False
    header_done = False

    # Status priority for tie-breaking: higher = more advanced
    status_priority = {
        "Completata": 4,
        "In corso": 3,
        "Bloccata": 2,
        "Da iniziare": 1,
        "Annullata": 0,
        "Sospesa": 0,
    }

    for line in lines:
        # Detect transition into "Stato Task" table
        if line.startswith("## Stato Task"):
            in_state_table = True
            header_lines.append(line)
            continue

        if in_state_table and not state_table_done:
            # Match task row: | T-XXX | ... | NN% | Status | ... |
            m = re.match(r"^\|\s*(T-[A-Z0-9-]+)\s*\|", line)
            if m:
                task_id = m.group(1).strip()
                # Find progress % in this row
                prog_m = re.search(r"\|\s*(\d+)\s*%\s*\|", line)
                progress = int(prog_m.group(1)) if prog_m else 0
                # Find status (after progress)
                status_m = re.search(r"\|\s*\d+\s*%\s*\|\s*([^|]+?)\s*\|", line)
                status = status_m.group(1).strip() if status_m else "Da iniziare"
                status_pri = status_priority.get(status, 0)
                tasks[task_id] = (progress, status_pri, line)
                continue
            # If we hit a non-table line after rows, table is done
            if line.strip().startswith("##") or (line.strip() == "" and tasks and not state_table_done):
                # Check if next significant section
                if line.strip().startswith("##"):
                    state_table_done = True
                    footer_lines.append(line)
                    continue
            # Keep table headers (--- separator, | ID | ... |) in header_lines
            if not tasks:
                header_lines.append(line)
            elif line.strip() == "":
                # Empty line inside table region — could be end of table
                continue
            else:
                # Non-task content — append to footer
                state_table_done = True
                footer_lines.append(line)
        elif state_table_done:
            footer_lines.append(line)
        else:
            header_lines.append(line)

    return "\n".join(header_lines), tasks, "\n".join(footer_lines)


def aggregate(files: list[Path]) -> str:
    """Aggregate multiple PROGRESS files using highest progress wins."""
    base_header = None
    base_footer = None
    base_file_used = None
    aggregated_tasks: dict[str, tuple[int, int, str]] = {}
    task_winning_branch: dict[str, str] = {}

    for f in files:
        content = f.read_text(encoding="utf-8")
        header, tasks, footer = parse_progress(content)
        branch_name = f.stem.replace("feature-", "feature/")

        # Use the file with most tasks as the base for header/footer template
        if base_header is None or len(tasks) > len(aggregated_tasks):
            base_header = header
            base_footer = footer
            base_file_used = f.name

        for task_id, (progress, status_pri, row) in tasks.items():
            if task_id not in aggregated_tasks:
                aggregated_tasks[task_id] = (progress, status_pri, row)
                task_winning_branch[task_id] = branch_name
                continue

            current_prog, current_pri, _ = aggregated_tasks[task_id]
            # Higher progress wins
            if progress > current_prog:
                aggregated_tasks[task_id] = (progress, status_pri, row)
                task_winning_branch[task_id] = branch_name
            elif progress == current_prog and status_pri > current_pri:
                aggregated_tasks[task_id] = (progress, status_pri, row)
                task_winning_branch[task_id] = branch_name

    # Sort tasks by ID
    sorted_tasks = sorted(
        aggregated_tasks.items(),
        key=lambda x: (x[0].replace("T-MERGE-", "T-99-").replace("T-", ""), x[0]),
    )

    # Recalculate metrics
    total = len(sorted_tasks)
    completed = sum(1 for _, (p, _, _) in sorted_tasks if p == 100)
    in_progress = sum(1 for _, (p, s, _) in sorted_tasks if 0 < p < 100 or (p == 0 and s == 3))
    bloccate = sum(1 for _, (_, s, _) in sorted_tasks if s == 2)
    da_iniziare = sum(1 for _, (p, s, _) in sorted_tasks if p == 0 and s == 1)
    overall = round(sum(p for _, (p, _, _) in sorted_tasks) / max(total, 1))

    # Update header riepilogo metrics
    if base_header:
        new_header = re.sub(r"\| Task totali \|.*?\|", f"| Task totali | {total} |", base_header)
        new_header = re.sub(r"\| Completate \|.*?\|", f"| Completate | {completed} |", new_header)
        new_header = re.sub(r"\| In corso \|.*?\|", f"| In corso | {in_progress} |", new_header)
        new_header = re.sub(r"\| Da iniziare \|.*?\|", f"| Da iniziare | {da_iniziare} |", new_header)
        new_header = re.sub(r"\| Bloccate \|.*?\|", f"| Bloccate | {bloccate} |", new_header)
        new_header = re.sub(r"\| Progresso complessivo \|.*?\|", f"| Progresso complessivo | {overall}% |", new_header)
        # Update last updated
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_header = re.sub(r"(Ultimo aggiornamento:.*?)\n", f"Ultimo aggiornamento: `{now}` (aggregato cross-branch)\n", new_header)
    else:
        new_header = "# Progresso Implementazione\n\n"

    # Build the output
    out = [new_header]
    for task_id, (_, _, row) in sorted_tasks:
        out.append(row)
    out.append(base_footer if base_footer else "")

    return "\n".join(out)


if __name__ == "__main__":
    print(
        "[DEPRECATED] aggregate-progress.py is no longer part of the SDLC progress flow.\n"
        "The progress model is centralized: PROGRESS.md/PROGRESS.xlsx live on 'main' of the\n"
        "specs/profiles repo and are read directly (git show origin/main:...). Cross-branch\n"
        "'highest-progress-wins' aggregation contradicts that model and is disabled.\n"
        "See skills/sdlc-progress-report/SKILL.md.",
        file=sys.stderr,
    )
    sys.exit(2)
    # --- legacy implementation retained below for reference (unreachable) ---
    if len(sys.argv) < 3:
        print("Usage: aggregate-progress.py <input-dir> <output-file>", file=sys.stderr)
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    files = sorted(input_dir.glob("*.md"))
    print(f"Aggregating {len(files)} files...", file=sys.stderr)
    result = aggregate(files)
    output_file.write_text(result, encoding="utf-8")
    print(f"Written {output_file}", file=sys.stderr)
