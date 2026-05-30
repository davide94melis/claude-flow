"""
golden-compare-gap.py

Comparatore DETERMINISTICO di due gap report prodotti da sdlc-analyzer nei due
rami di orchestrazione (`classic` vs `deep`), per il golden-test §11 del design
docs/ORCHESTRATION_INTEGRATION_DESIGN.md.

L'analisi gap e' LLM-driven (non deterministica): questo script NON rifa' l'analisi,
si limita a fare un diff RUBRIC-BASED tra le due "## Matrice di verifica" gia'
prodotte. Misura la divergenza (rischio V5) in modo riproducibile:

  - copertura: requisiti presenti in entrambi / solo classic / solo deep
  - accordo classificazioni: per i requisiti condivisi, Stato classic vs Stato deep
  - gap (Parziale/Mancante/Discrepanza/Da chiarire) trovati solo da un ramo
  - riepilogo numerico + esito euristico (deep dovrebbe coprire >= classic)

Uso:
  python scripts/golden-compare-gap.py <classic.md> <deep.md> [--out report.md]

Esce con codice 0 sempre (e' uno strumento di misura, non un gate automatico:
il giudizio "divergenza spiegabile?" resta umano). Esce 1 solo su errore di parsing.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

STATI = ["Coperto", "Parziale", "Mancante", "Discrepanza", "Da chiarire"]
# Stati che rappresentano un gap (qualcosa da fare / da chiarire)
GAP_STATI = {"Parziale", "Mancante", "Discrepanza", "Da chiarire"}

MATRIX_HEADING_RE = re.compile(r"^##+\s*Matrice di verifica", re.IGNORECASE)


def _strip_md(text: str) -> str:
    """Rimuove enfasi markdown e backtick, normalizza spazi."""
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return " ".join(text.split()).strip()


def _norm_key(requisito: str) -> str:
    """Chiave normalizzata per accoppiare i requisiti tra i due report:
    lowercase, accenti rimossi, solo alfanumerici+spazi, spazi collassati."""
    s = _strip_md(requisito).lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split()).strip()


def _norm_stato(cell: str) -> str:
    """Mappa una cella Stato a uno dei valori canonici (o 'Sconosciuto')."""
    c = _strip_md(cell).lower()
    # 'Da chiarire' contiene spazio: controlla per primo
    if "da chiarire" in c:
        return "Da chiarire"
    for s in ["Coperto", "Parziale", "Mancante", "Discrepanza"]:
        if s.lower() in c:
            return s
    return "Sconosciuto"


def _split_row(line: str) -> list[str]:
    """Spezza una riga di tabella markdown in celle (rimuove i pipe esterni)."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{2,}", line)) and set(line.strip()) <= set("|-: ")


def parse_matrix(md_path: Path) -> dict[str, dict]:
    """Estrae dalla '## Matrice di verifica' un dict {key_requisito: {requisito, stato}}.

    Robusto rispetto al numero variabile di colonne-repo: individua le colonne
    'Requisito' e 'Stato' dall'header, non per posizione fissa.
    """
    if not md_path.exists():
        raise SystemExit(f"ERRORE: file non trovato: {md_path}")
    lines = md_path.read_text(encoding="utf-8").splitlines()

    # 1. localizza la sezione matrice
    start = None
    for i, ln in enumerate(lines):
        if MATRIX_HEADING_RE.match(ln):
            start = i
            break
    if start is None:
        raise SystemExit(f"ERRORE: sezione '## Matrice di verifica' non trovata in {md_path}")

    # 2. fine sezione = prossima heading '##'
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    # 3. trova header (riga con 'Requisito' e 'Stato') + separatore
    header_idx = None
    for i in range(start + 1, end):
        ln = lines[i]
        if ln.lstrip().startswith("|") and "requisito" in ln.lower() and "stato" in ln.lower():
            header_idx = i
            break
    if header_idx is None:
        raise SystemExit(f"ERRORE: header della matrice (con 'Requisito' e 'Stato') non trovato in {md_path}")

    headers = [_strip_md(h).lower() for h in _split_row(lines[header_idx])]
    try:
        req_idx = next(i for i, h in enumerate(headers) if h == "requisito")
    except StopIteration:
        req_idx = 0
    try:
        stato_idx = next(i for i, h in enumerate(headers) if h == "stato")
    except StopIteration:
        raise SystemExit(f"ERRORE: colonna 'Stato' non individuabile nell'header di {md_path}")

    # 4. righe dati (dopo l'eventuale separatore)
    rows: dict[str, dict] = {}
    for i in range(header_idx + 1, end):
        ln = lines[i]
        if not ln.lstrip().startswith("|"):
            if ln.strip() == "":
                continue
            break  # tabella finita
        if _is_separator(ln):
            continue
        cells = _split_row(ln)
        if len(cells) <= max(req_idx, stato_idx):
            continue
        requisito = _strip_md(cells[req_idx])
        if not requisito or requisito.lower() == "requisito":
            continue
        key = _norm_key(requisito)
        if not key:
            continue
        rows[key] = {"requisito": requisito, "stato": _norm_stato(cells[stato_idx])}
    return rows


def build_report(classic: dict[str, dict], deep: dict[str, dict]) -> tuple[str, dict]:
    ck, dk = set(classic), set(deep)
    only_classic = sorted(ck - dk)
    only_deep = sorted(dk - ck)
    shared = sorted(ck & dk)

    agree, disagree = [], []
    for k in shared:
        cs, ds = classic[k]["stato"], deep[k]["stato"]
        (agree if cs == ds else disagree).append((k, cs, ds))

    def gaps(d: dict[str, dict]) -> set[str]:
        return {k for k, v in d.items() if v["stato"] in GAP_STATI}

    gaps_classic, gaps_deep = gaps(classic), gaps(deep)
    gaps_only_deep = sorted(gaps_deep - gaps_classic)
    gaps_only_classic = sorted(gaps_classic - gaps_deep)

    out = []
    out.append("# Golden-test gap comparison — classic vs deep\n")
    out.append("> Confronto deterministico delle '## Matrice di verifica'. L'analisi è LLM-driven:")
    out.append("> la divergenza qui misurata va giudicata **spiegabile o no** da un umano (gate §11).\n")

    out.append("## Copertura requisiti\n")
    out.append(f"- Requisiti in classic: **{len(classic)}**")
    out.append(f"- Requisiti in deep: **{len(deep)}**")
    out.append(f"- Condivisi: **{len(shared)}**")
    out.append(f"- Solo in deep ({len(only_deep)}): " + (", ".join(deep[k]['requisito'] for k in only_deep) or "—"))
    out.append(f"- Solo in classic ({len(only_classic)}): " + (", ".join(classic[k]['requisito'] for k in only_classic) or "—"))
    out.append("")

    out.append("## Accordo classificazioni (requisiti condivisi)\n")
    out.append(f"- Accordo: **{len(agree)}/{len(shared)}**")
    out.append(f"- Disaccordo: **{len(disagree)}/{len(shared)}**\n")
    if disagree:
        out.append("| Requisito | Stato classic | Stato deep |")
        out.append("|---|---|---|")
        for k, cs, ds in disagree:
            out.append(f"| {deep.get(k, classic[k])['requisito']} | {cs} | {ds} |")
        out.append("")

    out.append("## Gap (Parziale/Mancante/Discrepanza/Da chiarire)\n")
    out.append(f"- Gap totali classic: **{len(gaps_classic)}** · deep: **{len(gaps_deep)}**")
    out.append(f"- Gap trovati solo da deep ({len(gaps_only_deep)}): " + (", ".join(deep[k]['requisito'] for k in gaps_only_deep) or "—"))
    out.append(f"- Gap trovati solo da classic ({len(gaps_only_classic)}): " + (", ".join(classic[k]['requisito'] for k in gaps_only_classic) or "—"))
    out.append("")

    # Esito euristico (NON un gate automatico)
    deep_covers_more = len(deep) >= len(classic)
    out.append("## Esito euristico\n")
    out.append(f"- deep copre ≥ classic per numero di requisiti: **{'SÌ' if deep_covers_more else 'NO ⚠️'}**")
    out.append(f"- divergenza classificazioni: **{len(disagree)}** righe (vanno spiegate una a una)")
    if not deep_covers_more:
        out.append("- ⚠️ deep copre MENO requisiti di classic: indagare (il pattern deep dovrebbe trovare di più, non di meno).")
    out.append("\n> Decisione §11: procedere a step 4–5 solo se ogni divergenza è spiegabile (es. Mancante→Coperto giustificato da controprova adversarial). Altrimenti correggere il pattern.")

    summary = {
        "classic_count": len(classic), "deep_count": len(deep), "shared": len(shared),
        "only_deep": len(only_deep), "only_classic": len(only_classic),
        "agree": len(agree), "disagree": len(disagree),
        "gaps_classic": len(gaps_classic), "gaps_deep": len(gaps_deep),
        "gaps_only_deep": len(gaps_only_deep), "gaps_only_classic": len(gaps_only_classic),
        "deep_covers_more": deep_covers_more,
    }
    return "\n".join(out) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Confronto deterministico di due gap report classic vs deep (golden-test).")
    ap.add_argument("classic", type=Path, help="Path al gap report del ramo classic (.md)")
    ap.add_argument("deep", type=Path, help="Path al gap report del ramo deep (.md)")
    ap.add_argument("--out", type=Path, default=None, help="Scrive il report di confronto su file (oltre a stdout)")
    args = ap.parse_args(argv)

    # stdout/stderr in UTF-8 (la console Windows usa cp1252 e non stampa ≥/—/⚠️)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    classic = parse_matrix(args.classic)
    deep = parse_matrix(args.deep)
    report, summary = build_report(classic, deep)

    print(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"[scritto] {args.out}", file=sys.stderr)
    # riepilogo compatto su stderr (utile per script/CI)
    print("SUMMARY " + " ".join(f"{k}={v}" for k, v in summary.items()), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
