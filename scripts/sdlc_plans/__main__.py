"""Riga di comando del lettore dei piani: ``discover`` e ``read``.

    sdlc_plans discover (--stdin | --root DIR) [--format tsv|json]
    sdlc_plans read --plan PATH [--tasks F] [--progress F] [--plan-md F] [--estimate F]

Qui solo argomenti e I/O: la logica sta nel pacchetto. Uscite: 0 ok, 2 errore
d'uso (argomenti sbagliati, cartella o file non leggibili). Testo in UTF-8
con ``\\n`` a capo, su qualsiasi sistema.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .discovery import discover_plans, walk_repo
from .model import PlanRef
from .schedule import read_schedule
from .serialize import to_jsonable
from .tasks import read_plan


def _use_utf8() -> None:
    """Forza UTF-8 sui flussi standard: le pipe di Windows usano la codepage locale.

    Lo stdin sostituisce i byte non UTF-8 invece di cadere: un percorso illeggibile
    non deve far perdere l'elenco di tutti gli altri piani.
    """
    for stream, options in (
        (sys.stdin, {"encoding": "utf-8", "errors": "replace"}),
        (sys.stdout, {"encoding": "utf-8", "newline": "\n"}),
        (sys.stderr, {"encoding": "utf-8", "newline": "\n"}),
    ):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(**options)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdlc_plans", description="Lettore dei piani sdlc-suite.")
    commands = parser.add_subparsers(dest="command", required=True)

    discover = commands.add_parser("discover", help="elenca i piani trovati in un elenco di percorsi")
    source = discover.add_mutually_exclusive_group(required=True)
    source.add_argument("--stdin", action="store_true", help="percorsi dei file, uno per riga, da stdin")
    source.add_argument("--root", metavar="DIR", help="cartella locale da percorrere")
    discover.add_argument("--format", choices=("tsv", "json"), default="tsv")

    read = commands.add_parser("read", help="legge un piano e ne stampa task e calendario in JSON")
    read.add_argument("--plan", required=True, metavar="PATH", help="percorso del piano (solo come etichetta)")
    read.add_argument("--tasks", metavar="F", help="file TASKS.md")
    read.add_argument("--progress", metavar="F", help="file PROGRESS.md")
    read.add_argument("--plan-md", metavar="F", help="file PLAN.md")
    read.add_argument("--estimate", metavar="F", help="file ESTIMATE.md")
    return parser


def _paths_from_stdin() -> list[str]:
    lines = (line.strip() for line in sys.stdin)
    return [line for line in lines if line]


def _tsv_line(plan: PlanRef) -> str:
    return "\t".join((plan.path, plan.state, plan.wave or "", ",".join(plan.files)))


def _dump(value: object) -> str:
    return json.dumps(to_jsonable(value), ensure_ascii=False, indent=2)


def _discover(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.stdin:
        paths = _paths_from_stdin()
    else:
        if not Path(args.root).is_dir():
            parser.error(f"--root non e' una cartella: {args.root}")
        paths = walk_repo(Path(args.root))
    plans = discover_plans(paths)
    if args.format == "json":
        sys.stdout.write(_dump(plans) + "\n")
    else:
        sys.stdout.write("".join(_tsv_line(plan) + "\n" for plan in plans))


def _read_document(parser: argparse.ArgumentParser, path: str | None) -> str | None:
    """Testo del file; ``None`` se non e' stato indicato o non esiste (con un avviso)."""
    if path is None:
        return None
    try:
        # utf-8-sig: un file salvato con BOM si legge come gli altri.
        return Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"file non trovato, trattato come assente: {path}", file=sys.stderr)
        return None
    except (OSError, UnicodeDecodeError) as error:
        parser.error(f"file non leggibile come UTF-8: {path} ({error})")


def _read(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    tasks, progress, plan_md, estimate = (
        _read_document(parser, path) for path in (args.tasks, args.progress, args.plan_md, args.estimate)
    )
    result = {
        "plan_tasks": read_plan(args.plan, tasks, progress),
        "schedule": read_schedule({"PLAN.md": plan_md, "ESTIMATE.md": estimate}),
    }
    sys.stdout.write(_dump(result) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "discover":
        _discover(parser, args)
    else:
        _read(parser, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
