"""Da oggetti del modello a strutture JSON (solo libreria standard)."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date

from .model import PlanTasks


def to_jsonable(obj: object) -> object:
    """Copia di ``obj`` fatta solo di dict, liste e scalari, pronta per ``json.dumps``.

    Una dataclass diventa un dict dei suoi campi (``PlanTasks`` aggiunge anche la
    proprieta' ``degraded``), tuple e liste diventano liste, un ``date`` diventa
    la stringa ISO. Gli altri scalari restano com'erano. Non modifica ``obj``.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        converted = {field.name: to_jsonable(getattr(obj, field.name)) for field in fields(obj)}
        if isinstance(obj, PlanTasks):
            converted["degraded"] = obj.degraded
        return converted
    if isinstance(obj, (tuple, list)):
        return [to_jsonable(item) for item in obj]
    if isinstance(obj, Mapping):
        return {key: to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, date):
        return obj.isoformat()
    return obj
