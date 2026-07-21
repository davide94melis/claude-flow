#!/usr/bin/env python3
"""Helper atomico per il changelog globale per-progetto (miglioria #3).

Manutiene `CHANGELOG.md` alla root della repo specifiche/profilo: un indice
`## Piani` (tabella upsert per-piano) + un feed `## Attività` append-only,
newest-first, raggruppato per data (`### YYYY-MM-DD`). Nessuna dipendenza esterna
(solo stdlib), grep-compatibile, niente jq. Le scritture sono idempotenti: un
doppio append della stessa voce non duplica.

Contratto di scrittura condiviso: vedi
skills/sdlc-executor/references/CHANGELOG-contract.md — usato da sdlc-executor
(writer primario) e appeso da sdlc-debug / sdlc-updater / sdlc-merge /
sdlc-verifier secondo il contratto.

Sottocomandi:
  init         --file F --project NAME
               crea il CHANGELOG se assente (no-op se esiste).
  upsert-plan  --file F --plan P [--status S] [--period X] [--tasks "3/8"]
               [--progress PATH] [--summary "1 line"]
               inserisce/aggiorna la riga indice del piano (chiave = --plan).
  add-activity --file F --date YYYY-MM-DD --line "markdown line"
               antepone una voce nel feed sotto la data (idempotente per linea).
  task         --file F --date D --id T-003 --area BE --summary "..." --plan P
               [--commits "BE@1a2b3c4,FE@9a8b7c6"] [--progress PATH]
               scorciatoia: compone e appende la voce-task standard.
  plan-done    --file F --date D --plan P --done N --tot M [--bugs K]
               [--range "BE@aaa..bbb"] [--progress PATH]
               scorciatoia: compone e appende la entry "PLAN DONE".

Uso tipico (executor): pull -> questo script -> commit -> push (single-writer).
"""
import argparse
import os
import sys

HEADER_TMPL = """# Changelog — {project}
> Synthetic cross-plan index. Auto-updated by sdlc-executor (+ shared write-contract). Append-only.
> For details follow the PROGRESS / commit links.

## Piani
| Plan | Status | Period | Tasks done/tot | PROGRESS | Summary (1 line) |
|---|---|---|---|---|---|

## Attività (recent → old)
"""

PLANS_HEADER = "## Piani"
ACTIVITY_HEADER = "## Attività (recent → old)"
TABLE_SEP = "|---|---|---|---|---|---|"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def atomic_write(path: str, content: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


def ensure(path: str, project: str) -> str:
    if os.path.exists(path):
        return read(path)
    content = HEADER_TMPL.format(project=project or "progetto")
    atomic_write(path, content)
    return content


def split_lines(text: str) -> list:
    return text.splitlines()


def find_line(lines: list, predicate) -> int:
    for i, ln in enumerate(lines):
        if predicate(ln):
            return i
    return -1


def cmd_init(args) -> int:
    ensure(args.file, args.project)
    print(f"[changelog] init ok: {args.file}")
    return 0


def cmd_upsert_plan(args) -> int:
    text = ensure(args.file, args.project or "")
    lines = split_lines(text)
    plan = args.plan.strip()
    row = "| {plan} | {status} | {period} | {tasks} | {progress} | {summary} |".format(
        plan=plan,
        status=(args.status or "").strip(),
        period=(args.period or "").strip(),
        tasks=(args.tasks or "").strip(),
        progress=(args.progress or "").strip(),
        summary=(args.summary or "").strip().replace("\n", " "),
    )
    sep_idx = find_line(lines, lambda ln: ln.strip() == TABLE_SEP)
    if sep_idx == -1:
        print("[changelog] ERROR: Piani table not found", file=sys.stderr)
        return 2
    # existing row for this plan? (first cell equals plan)
    existing = -1
    for i in range(sep_idx + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("## "):
            break
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if cells and cells[0] == plan:
                existing = i
                break
    if existing != -1:
        lines[existing] = row
    else:
        # append right after the separator (most-recently-touched near top)
        lines.insert(sep_idx + 1, row)
    atomic_write(args.file, "\n".join(lines) + "\n")
    print(f"[changelog] upsert-plan ok: {plan}")
    return 0


def cmd_add_activity(args) -> int:
    text = ensure(args.file, args.project or "")
    lines = split_lines(text)
    date = args.date.strip()
    line = args.line.rstrip()
    if not line.startswith("- "):
        line = "- " + line
    # idempotency: exact line already present anywhere -> no-op
    if any(ln.rstrip() == line for ln in lines):
        print("[changelog] add-activity: duplicate, no-op")
        return 0
    act_idx = find_line(lines, lambda ln: ln.strip() == ACTIVITY_HEADER)
    if act_idx == -1:
        print("[changelog] ERROR: Attività section not found", file=sys.stderr)
        return 2
    date_marker = f"### {date}"
    # find the date section within Attività
    date_idx = -1
    for i in range(act_idx + 1, len(lines)):
        if lines[i].strip() == date_marker:
            date_idx = i
            break
    if date_idx != -1:
        # prepend under this date (newest-first within the day)
        lines.insert(date_idx + 1, line)
    else:
        # insert a new date section in the right position (newest-first)
        insert_at = act_idx + 1
        # skip a single blank line right after the header if present
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        placed = False
        i = act_idx + 1
        while i < len(lines):
            ln = lines[i].strip()
            if ln.startswith("### "):
                other = ln[4:].strip()
                # dates are ISO YYYY-MM-DD -> lexicographic == chronological
                if date > other:
                    insert_at = i
                    placed = True
                    break
            elif ln.startswith("## "):
                insert_at = i
                placed = True
                break
            i += 1
        if not placed:
            insert_at = len(lines)
        block = [date_marker, line, ""]
        lines[insert_at:insert_at] = block
    atomic_write(args.file, "\n".join(lines) + "\n")
    print(f"[changelog] add-activity ok ({date})")
    return 0


def _commits_str(commits: str) -> str:
    if not commits:
        return ""
    parts = [c.strip() for c in commits.split(",") if c.strip()]
    if not parts:
        return ""
    joined = ", ".join(f"`{p}`" for p in parts)
    return f" — commit: {joined}"


def cmd_task(args) -> int:
    prog = f" — → {args.progress}#{args.id}" if args.progress else ""
    line = "- **{id}** [{area}] {summary} — *plan: {plan}*{commits}{prog}".format(
        id=args.id.strip(),
        area=(args.area or "").strip(),
        summary=args.summary.strip(),
        plan=args.plan.strip(),
        commits=_commits_str(args.commits or ""),
        prog=prog,
    )
    ns = argparse.Namespace(file=args.file, date=args.date, line=line,
                            project=args.project or "")
    return cmd_add_activity(ns)


def cmd_plan_done(args) -> int:
    bugs = args.bugs if args.bugs is not None else 0
    rng = f" — commit range {args.range}" if args.range else ""
    prog = f" — → {args.progress}" if args.progress else ""
    line = "- **✔ PLAN DONE** {plan} — {done}/{tot} tasks, {bugs} open bugs{rng}{prog}".format(
        plan=args.plan.strip(), done=args.done, tot=args.tot, bugs=bugs, rng=rng, prog=prog,
    )
    ns = argparse.Namespace(file=args.file, date=args.date, line=line,
                            project=args.project or "")
    return cmd_add_activity(ns)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Global per-project changelog helper (SDLC #3).")
    # --project (bootstrap header only) lives on `common` → pass it AFTER the subcommand,
    # e.g. `changelog.py init --file F --project NAME`.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default="", help="project name (for bootstrap header)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", parents=[common])
    s.add_argument("--file", required=True); s.set_defaults(func=cmd_init)

    s = sub.add_parser("upsert-plan", parents=[common])
    s.add_argument("--file", required=True); s.add_argument("--plan", required=True)
    s.add_argument("--status", default=""); s.add_argument("--period", default="")
    s.add_argument("--tasks", default=""); s.add_argument("--progress", default="")
    s.add_argument("--summary", default=""); s.set_defaults(func=cmd_upsert_plan)

    s = sub.add_parser("add-activity", parents=[common])
    s.add_argument("--file", required=True); s.add_argument("--date", required=True)
    s.add_argument("--line", required=True); s.set_defaults(func=cmd_add_activity)

    s = sub.add_parser("task", parents=[common])
    s.add_argument("--file", required=True); s.add_argument("--date", required=True)
    s.add_argument("--id", required=True); s.add_argument("--area", default="")
    s.add_argument("--summary", required=True); s.add_argument("--plan", required=True)
    s.add_argument("--commits", default=""); s.add_argument("--progress", default="")
    s.set_defaults(func=cmd_task)

    s = sub.add_parser("plan-done", parents=[common])
    s.add_argument("--file", required=True); s.add_argument("--date", required=True)
    s.add_argument("--plan", required=True); s.add_argument("--done", required=True)
    s.add_argument("--tot", required=True); s.add_argument("--bugs", type=int, default=0)
    s.add_argument("--range", default=""); s.add_argument("--progress", default="")
    s.set_defaults(func=cmd_plan_done)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
