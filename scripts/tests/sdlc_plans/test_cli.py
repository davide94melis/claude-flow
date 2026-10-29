"""Test della riga di comando `sdlc_plans` e della serializzazione JSON.

La CLI si lancia dallo script `sdlc-plans.py`: gli interpreti isolati
(`python312._pth`, ad esempio la distribuzione embeddable su Windows) ignorano
PYTHONPATH e non mettono la cartella dello script in `sys.path`, quindi
`python -m sdlc_plans` non vi funziona; il lanciatore aggiunge da solo la sua cartella.
"""
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from sdlc_plans import PlanTasks, Schedule, to_jsonable, read_plan, read_schedule

SCRIPTS = Path(__file__).resolve().parents[2]
LAUNCHER = SCRIPTS / "sdlc-plans.py"
W = "plans/in-progress/2026-07-29_wave-x"
NESTED = [f"{W}/ESTIMATE.md", f"{W}/sub-a/TASKS.md", f"{W}/sub-a/PROGRESS.md", f"{W}/sub-a/TASKS.en.md",
          f"{W}/sub-c/PROGRESS.md", f"{W}/_artifacts/merge-release/INTEGRATION.md", "CHANGELOG.md"]
NESTED_TSV = [
    f"{W}/sub-a\tin-progress\t2026-07-29_wave-x\tPROGRESS.md,TASKS.en.md,TASKS.md",
    f"{W}/sub-c\tin-progress\t2026-07-29_wave-x\tPROGRESS.md"]

# Senza queste due variabili Python userebbe la codifica della console (cp1252 su
# Windows): cosi' il test prova davvero che la CLI forza UTF-8 da sola.
_ENCODING_VARS = ("PYTHONIOENCODING", "PYTHONUTF8")


def _env():
    return {k: v for k, v in os.environ.items() if k not in _ENCODING_VARS}


def cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(LAUNCHER), *args], input=stdin, capture_output=True,
                          text=True, encoding="utf-8", env=_env())


def cli_bytes(*args, stdin=b""):
    return subprocess.run([sys.executable, str(LAUNCHER), *args], input=stdin, capture_output=True,
                          env=_env())


def test_cli_discover_stdin_tsv():
    r = cli("discover", "--stdin", stdin="\n".join(NESTED))
    assert r.returncode == 0
    assert r.stdout.splitlines() == NESTED_TSV


def test_cli_discover_root_json(plans_fixtures):
    plans = json.loads(cli("discover", "--root", str(plans_fixtures / "flat"), "--format", "json").stdout)
    assert [p["state"] for p in plans] == ["draft", "in-progress"]


def test_cli_read_outputs_json_with_warnings_and_schedule(plans_fixtures):
    d = plans_fixtures / "nested" / W
    out = json.loads(cli("read", "--plan", f"{W}/sub-a", "--tasks", str(d / "sub-a/TASKS.md"),
                         "--progress", str(d / "sub-a/PROGRESS.md"), "--estimate", str(d / "ESTIMATE.md")).stdout)
    assert out["plan_tasks"]["rows_read"] == 14 and out["plan_tasks"]["degraded"] is False
    assert "status_unknown" in {w["code"] for w in out["plan_tasks"]["warnings"]}
    assert out["schedule"]["deadline"] == "2026-10-16"


def test_cli_bad_usage_exit_2():
    assert cli("discover").returncode == 2


def test_cli_module_form_works_where_package_is_importable():
    code = ("import runpy, sys; sys.path.insert(0, r'%s'); sys.argv = ['sdlc_plans', 'discover', '--stdin']; "
            "runpy.run_module('sdlc_plans', run_name='__main__', alter_sys=True)" % SCRIPTS)
    r = subprocess.run([sys.executable, "-c", code], input="\n".join(NESTED), capture_output=True,
                       text=True, encoding="utf-8", env=_env())
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == NESTED_TSV


def test_cli_discover_stdin_accepts_crlf_and_blank_lines():
    raw = ("\r\n".join(NESTED) + "\r\n\r\n   \r\n").encode("utf-8")
    r = cli_bytes("discover", "--stdin", stdin=raw)
    assert r.returncode == 0
    assert r.stdout.decode("utf-8").splitlines() == NESTED_TSV


def test_cli_discover_stdin_with_undecodable_bytes_does_not_crash():
    # R29: un byte non UTF-8 sulla riga di un percorso non deve far cadere la scoperta dei piani.
    raw = "\n".join(NESTED).encode("utf-8") + b"\nplans/todo/2026-10-05_x\xff\xfe/TASKS.md\n"
    r = cli_bytes("discover", "--stdin", stdin=raw)
    assert r.returncode == 0, r.stderr
    assert b"Traceback" not in r.stderr
    lines = r.stdout.decode("utf-8").splitlines()
    assert lines[:2] == NESTED_TSV and len(lines) == 3


def test_cli_discover_stdin_empty_input_prints_nothing():
    r = cli("discover", "--stdin", stdin="")
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")
    r = cli("discover", "--stdin", "--format", "json", stdin="")
    assert (r.returncode, json.loads(r.stdout)) == (0, [])


def test_cli_discover_stdin_json_lists_planrefs():
    plans = json.loads(cli("discover", "--stdin", "--format", "json", stdin="\n".join(NESTED)).stdout)
    assert plans[0] == {"path": f"{W}/sub-a", "state": "in-progress", "wave": "2026-07-29_wave-x",
                        "name": "sub-a", "files": ["PROGRESS.md", "TASKS.en.md", "TASKS.md"]}


def test_cli_output_is_utf8_with_lf_newlines():
    folder = "plans/todo/2026-10-05_perché"
    r = cli_bytes("discover", "--stdin", stdin=f"{folder}/TASKS.md\n".encode("utf-8"))
    assert r.returncode == 0
    assert r.stdout == f"{folder}\ttodo\t\tTASKS.md\n".encode("utf-8")


def test_cli_discover_root_that_is_not_a_directory_exits_2(tmp_path):
    missing = tmp_path / "non-esiste"
    r = cli("discover", "--root", str(missing))
    assert r.returncode == 2 and r.stdout == ""
    assert str(missing) in r.stderr


def test_cli_discover_stdin_and_root_are_mutually_exclusive(tmp_path):
    assert cli("discover", "--stdin", "--root", str(tmp_path)).returncode == 2


def test_cli_discover_unknown_format_exits_2():
    assert cli("discover", "--stdin", "--format", "xml", stdin="").returncode == 2


def test_cli_read_requires_plan():
    assert cli("read").returncode == 2


def test_cli_read_json_keeps_emoji_unescaped(plans_fixtures):
    d = plans_fixtures / "nested" / W / "sub-a"
    r = cli("read", "--plan", f"{W}/sub-a", "--tasks", str(d / "TASKS.md"), "--progress", str(d / "PROGRESS.md"))
    assert r.returncode == 0
    assert "✅" in r.stdout and "\\u2705" not in r.stdout


def test_cli_read_missing_file_is_treated_as_absent(plans_fixtures):
    d = plans_fixtures / "nested" / W / "sub-a"
    missing = d / "NON-ESISTE.md"
    r = cli("read", "--plan", f"{W}/sub-a", "--tasks", str(d / "TASKS.md"), "--progress", str(missing),
            "--plan-md", str(d / "ALTRO-ASSENTE.md"))
    assert r.returncode == 0
    assert r.stderr.splitlines() == [f"file non trovato, trattato come assente: {missing}",
                                     f"file non trovato, trattato come assente: {d / 'ALTRO-ASSENTE.md'}"]
    out = json.loads(r.stdout)
    assert out["plan_tasks"]["rows_read"] > 0
    assert all(t["in_progress"] is False for t in out["plan_tasks"]["tasks"])


def test_cli_read_with_no_documents_gives_empty_plan_and_schedule():
    r = cli("read", "--plan", "plans/todo/x")
    assert r.returncode == 0 and r.stderr == ""
    out = json.loads(r.stdout)
    assert set(out) == {"plan_tasks", "schedule"}
    assert out["plan_tasks"]["tasks"] == [] and out["plan_tasks"]["degraded"] is False
    assert out["schedule"]["deadline"] is None and out["schedule"]["sources"] == {}


def test_cli_read_unreadable_file_exits_2(tmp_path):
    bad = tmp_path / "TASKS.md"
    bad.write_bytes(b"| ID |\n\xe8\n")  # latin-1, non UTF-8
    r = cli("read", "--plan", "plans/todo/x", "--tasks", str(bad))
    assert r.returncode == 2 and r.stdout == ""
    assert str(bad) in r.stderr


def test_cli_read_accepts_utf8_bom(plans_fixtures, tmp_path):
    d = plans_fixtures / "nested" / W / "sub-a"
    bom = tmp_path / "TASKS.md"
    bom.write_bytes(b"\xef\xbb\xbf" + (d / "TASKS.md").read_bytes())
    plain = json.loads(cli("read", "--plan", "p", "--tasks", str(d / "TASKS.md")).stdout)
    with_bom = json.loads(cli("read", "--plan", "p", "--tasks", str(bom)).stdout)
    assert with_bom["plan_tasks"]["rows_read"] == plain["plan_tasks"]["rows_read"] > 0


# --- to_jsonable -----------------------------------------------------------

def test_to_jsonable_scalars_pass_through():
    assert [to_jsonable(x) for x in (None, True, 3, 2.5, "ok")] == [None, True, 3, 2.5, "ok"]


def test_to_jsonable_converts_dates_tuples_and_dicts_recursively():
    value = {"day": date(2026, 10, 16), "pair": (1, (2, date(2026, 1, 2))), "inner": {"xs": [(1,)]}}
    assert to_jsonable(value) == {"day": "2026-10-16", "pair": [1, [2, "2026-01-02"]], "inner": {"xs": [[1]]}}


def test_to_jsonable_dataclass_becomes_dict_of_its_fields(plans_fixtures):
    d = plans_fixtures / "nested" / W
    schedule = read_schedule({"ESTIMATE.md": (d / "ESTIMATE.md").read_text(encoding="utf-8")})
    out = to_jsonable(schedule)
    assert isinstance(schedule, Schedule)
    assert out["deadline"] == "2026-10-16"
    assert out["start"] == (schedule.start.isoformat() if schedule.start else None)
    assert isinstance(out["milestones"], list) and isinstance(out["sources"], dict)
    json.dumps(out)  # tutto serializzabile


def test_to_jsonable_plan_tasks_includes_degraded_property(plans_fixtures):
    d = plans_fixtures / "nested" / W / "sub-a"
    plan = read_plan("p", (d / "TASKS.md").read_text(encoding="utf-8"), None)
    out = to_jsonable(plan)
    assert isinstance(plan, PlanTasks)
    assert out["degraded"] is plan.degraded
    assert out["tasks"][0]["activity"] == {"raw": plan.tasks[0].activity.raw, "value": plan.tasks[0].activity.value}
    degraded = to_jsonable(PlanTasks(plan="p", tasks=(), rows_seen=3, rows_read=2, warnings=()))
    assert degraded["degraded"] is True


def test_to_jsonable_does_not_mutate_its_input():
    value = {"xs": (1, 2)}
    to_jsonable(value)
    assert value == {"xs": (1, 2)}
