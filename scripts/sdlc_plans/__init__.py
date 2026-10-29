"""Lettore condiviso dei piani sdlc-suite (solo libreria standard)."""
from __future__ import annotations

from .discovery import PLAN_MARKERS, discover_plans, walk_repo
from .effort import MAX_EFFORT_DAYS, parse_effort
from .model import (
    Cell,
    Effort,
    Milestone,
    ParseWarning,
    PlanRef,
    PlanTasks,
    Schedule,
    Task,
)
from .schedule import DEADLINE_KINDS, FIXED_KEYS, merge_schedule, read_schedule
from .serialize import to_jsonable
from .tables import Row, Table, TableScan, scan_tables
from .tasks import read_plan
from .vocab import (
    OWNER_PLACEHOLDERS,
    STATUSES,
    TASK_ID_RE,
    canon_status,
    canonical_field,
    clean_markup,
    is_placeholder,
    norm_header,
    normalize_id,
    owner_base,
)

__all__ = [
    "Cell",
    "DEADLINE_KINDS",
    "Effort",
    "FIXED_KEYS",
    "MAX_EFFORT_DAYS",
    "Milestone",
    "OWNER_PLACEHOLDERS",
    "PLAN_MARKERS",
    "ParseWarning",
    "PlanRef",
    "PlanTasks",
    "Row",
    "STATUSES",
    "Schedule",
    "TASK_ID_RE",
    "Table",
    "TableScan",
    "Task",
    "canon_status",
    "canonical_field",
    "clean_markup",
    "discover_plans",
    "is_placeholder",
    "merge_schedule",
    "norm_header",
    "normalize_id",
    "owner_base",
    "parse_effort",
    "read_plan",
    "read_schedule",
    "scan_tables",
    "to_jsonable",
    "walk_repo",
]
