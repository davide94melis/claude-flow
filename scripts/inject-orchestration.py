"""
inject-orchestration.py

Step 2 di docs/ORCHESTRATION_INTEGRATION_DESIGN.md.

Inietta in modo IDEMPOTENTE la sezione condivisa "## Modalita' di orchestrazione"
in tutte e 9 le SKILL.md SDLC. La sezione e' il blocco di opt-in uniforme (cascata
di risoluzione flag>keyword>domanda, banner, capability check, mappa di fallback
deep->classic, invarianti) che permette a ogni skill di girare in modalita'
`classic` (default, sequenziale) o `deep` (Workflow tool multi-agent + adversarial).

Modellato su scripts/dualize-paths.py (stesso pattern: trova ancora -> inietta,
skip idempotente se gia' applicato).

Punto di iniezione (subito dopo il blocco condiviso "Risoluzione Path + detection
modalita'", §5 del design):
  - 8 skill standard: dopo la sezione "## Caricamento contesto progetto (CONST + PROFILE)"
  - sdlc-profile-setup (eccezione §7.6: non carica CONST+PROFILE, li crea):
    dopo lo "## Step 1.5 — Scelta modalita'" (la modalita' si risolve dopo lo Step MODE)

Idempotenza: se la skill contiene gia' la heading della sezione -> SKIP.

Nessuna dipendenza esterna. Rilanciarlo non duplica nulla.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Heading canonico della sezione iniettata. Usato anche per il check di idempotenza.
# Accentato per allinearsi al design doc e al corpo migrato delle skill.
ORCH_HEADING = "## Modalità di orchestrazione"

# ---------------------------------------------------------------------------
# Corpo della sezione (uniforme per tutte e 9 le skill -> vincolo V2 coerenza).
# Gli schema JSON dei workflow NON vivono qui ma negli script workflows/*.js (§9).
# NB: stringa NON raw -> '\\s' diventa '\s', '\\K' diventa '\K' nel markdown finale.
# ---------------------------------------------------------------------------
ORCH_BODY = """Ogni skill SDLC può girare in due modalità:

- **`classic`** (default) — esecuzione sequenziale, leggera, pochi token. È il comportamento storico.
- **`deep`** — orchestrazione parallela multi-agent (Workflow tool) + verifica adversariale: più lenta e costosa, ma più esaustiva.

> **Mai escalation silenziosa.** Non si passa a `deep` (con la relativa spesa) senza una scelta esplicita — flag persistente o conferma dell'utente. Default globale = `classic`.

### Risoluzione della modalità (cascata, in ordine di precedenza)

1. **Flag persistente** in `.sdlc-local.json` (fallback `.br-local.json`) — la sorgente automatica a precedenza più alta. Campi *flat* (grep-compatibili, niente `jq`):

   ```bash
   LOCAL_CFG=".sdlc-local.json"; [ -f "$LOCAL_CFG" ] || LOCAL_CFG=".br-local.json"
   ORCH_MODE=$(grep -oP '"orchestration_mode"\\s*:\\s*"\\K[^"]+' "$LOCAL_CFG" 2>/dev/null);  ORCH_MODE=${ORCH_MODE:-classic}
   ORCH_DEPTH=$(grep -oP '"orchestration_depth"\\s*:\\s*"\\K[^"]+' "$LOCAL_CFG" 2>/dev/null); ORCH_DEPTH=${ORCH_DEPTH:-standard}
   ORCH_MAXC=$(grep -oP '"orchestration_max_concurrency"\\s*:\\s*\\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_MAXC=${ORCH_MAXC:-10}
   ORCH_PANEL=$(grep -oP '"orchestration_verifier_panel"\\s*:\\s*\\K[0-9]+' "$LOCAL_CFG" 2>/dev/null); ORCH_PANEL=${ORCH_PANEL:-3}
   ```

2. **Keyword nel trigger** ("a fondo", "esaustivo", "in parallelo", "ultracode") — override per singola invocazione, ma **declassata sotto il flag**: una scelta `classic` deliberata nel flag NON viene scavalcata da una keyword ambigua. Ogni escalation verso `deep` innescata da keyword **passa da conferma esplicita** (AskUserQuestion) prima di spendere.

3. **AskUserQuestion** quando né flag né keyword hanno deciso. Con **auto-suggeritore**: se la dimensione del lavoro supera una soglia (≥3 repo, ≥25 task, ondata ≥8 bug, changelog AFU ampio) proponi `deep` mostrando il razionale, **ma la pre-selezione resta `classic`** (no spesa a sorpresa).

**`/effort ultracode` di sessione**: se attivo a livello sessione, la **prima** skill SDLC invocata chiede **una volta** se applicare `deep` a tutte le skill SDLC della sessione, poi ricorda la risposta.

### Banner di modalità (sempre a video prima del lavoro pesante)

- `deep`:  *"Eseguo in modalità Workflow+approfondita: ~N agent, più lento/costoso."*
- `classic`: *"Modalità classica (sequenziale)."*

### Esecuzione `deep` — invocazione del Workflow tool

In `deep`, la skill **istruisce Claude a invocare il Workflow tool**: con lo script dedicato in `workflows/` per le skill *heavy* (`sdlc-analyzer`, `sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-reviewer` — vero fan-out + `adversarial-verify` + `completeness-critic` + `isolation:'worktree'`), oppure con un singolo sub-step di `completeness/coherence-critic` per le skill *light* (`sdlc-estimator`, `sdlc-clarify`, `sdlc-progress-report`, `sdlc-profile-setup`). Gli schema JSON vivono **negli script `workflows/*.js`**, non qui.

### Capability check + degradazione (assume-disponibile + fallback esplicito)

**Nessun probe preventivo**: procedi assumendo il Workflow tool presente. Se l'invocazione **non è possibile** (tool assente) **oppure fallisce/non completa**:

1. banner a video: *"Workflow tool non disponibile: eseguo in modalità classica sequenziale."*;
2. prosegui nel ramo `classic` usando la mappa di fallback sotto;
3. inserisci in testa all'artefatto prodotto (PLAN/CLARIFY/gap report/...) il banner **"COPERTURA RIDOTTA — prodotto senza completeness-critic/adversarial-verify"**. La degradazione è **rumorosa**, mai silenziosa: gli artefatti `classic` e `deep` NON sono equivalenti.

> Due casi distinti: (a) **Workflow tool assente / non parte** → fallback completo a `classic` (sopra). (b) **Barriera parziale** (il workflow parte ma k/N agent falliscono) → lo script ritorna i k riusciti come *proposte non applicate*; i file source-of-truth NON vengono scritti parzialmente; l'agente principale presenta lo stato e l'utente decide.

### Mappa di fallback `deep` → `classic`

| Primitiva `deep` | Fallback `classic` |
|---|---|
| `parallel` / `pipeline` | loop sequenziale sugli stessi thunk (comportamento attuale) |
| `agent({agentType, schema})` | "leggi `~/.claude/agents/<agentType>.md` e lancia un Task" + parsing MD |
| `adversarial-verify` / `judge-panel` | singola verifica `sdlc-verifier` inline |
| `completeness-critic` | checklist manuale già presente nella skill |
| `loop-until-dry` | ciclo fix/riverifica già descritto |

### Invarianti inviolabili (in ENTRAMBE le modalità)

1. Tutti i gate di conferma utente ("mai procedere senza conferma").
2. Mai auto-commit sulle repo di **codice**.
3. Il sottoagente implementa, l'agente principale coordina.
4. Scritture sui file source-of-truth (PROGRESS, BUG_REPORT, CLARIFY, PLAN/TASKS) sempre **single-writer serializzato** (pull→edit→commit→push).
5. Gli agent di verifica/esplorazione restano **read-only**.
6. Barriere obbligatorie dove la fase a valle richiede lo stato completo."""

# Nota extra appesa solo a skill specifiche (divergenza per-skill minima, §7.6).
PROFILE_SETUP_NOTE = """

> **Nota per `sdlc-profile-setup` (eccezione §7.6):** questa skill **crea** `.sdlc-local.json`, non lo legge a monte come le altre. La modalità si risolve qui, dopo lo Step MODE: se un `.sdlc-local.json` (o `.br-local.json` legacy) esiste già nel codebase usa il suo `orchestration_mode`; altrimenti chiedi via AskUserQuestion (default `classic`). In `deep` il valore aggiunto è confinato a: auto-detect multi-repo con explorer + `completeness-critic` sul PROFILE prima della conferma (un PROFILE errato viene ereditato da tutte le altre 8 skill)."""

# ---------------------------------------------------------------------------
# Config per-skill: (skill_dir, anchor_prefix, extra_note)
# anchor_prefix = prefisso della heading "## " dopo la cui sezione iniettare.
# ---------------------------------------------------------------------------
STANDARD_ANCHOR = "## Caricamento contesto progetto"
PROFILE_ANCHOR = "## Step 1.5"

HEAVY = {"sdlc-analyzer", "sdlc-executor", "sdlc-debug", "sdlc-updater", "sdlc-reviewer"}

SKILLS = [
    ("sdlc-analyzer", STANDARD_ANCHOR, ""),
    ("sdlc-clarify", STANDARD_ANCHOR, ""),
    ("sdlc-debug", STANDARD_ANCHOR, ""),
    ("sdlc-estimator", STANDARD_ANCHOR, ""),
    ("sdlc-executor", STANDARD_ANCHOR, ""),
    ("sdlc-progress-report", STANDARD_ANCHOR, ""),
    ("sdlc-reviewer", STANDARD_ANCHOR, ""),
    ("sdlc-updater", STANDARD_ANCHOR, ""),
    ("sdlc-profile-setup", PROFILE_ANCHOR, PROFILE_SETUP_NOTE),
]


def build_block(extra_note: str) -> str:
    """Sezione completa pronta da inserire: heading + corpo + nota + separatore."""
    return f"{ORCH_HEADING}\n\n{ORCH_BODY}{extra_note}\n\n---\n"


def inject(content: str, anchor_prefix: str, extra_note: str) -> tuple[str, str]:
    """Inserisce la sezione subito prima della prima heading '## ' che segue la
    sezione-ancora. Idempotente: se gia' presente, ritorna invariato.

    Ritorna (nuovo_contenuto, status).
    """
    if ORCH_HEADING in content:
        return content, "SKIP (gia' iniettato)"

    lines = content.split("\n")

    # 1. trova la riga della heading-ancora
    anchor_idx = None
    for i, line in enumerate(lines):
        if line.startswith(anchor_prefix):
            anchor_idx = i
            break
    if anchor_idx is None:
        raise RuntimeError(f"ancora '{anchor_prefix}' non trovata")

    # 2. trova la prima heading '## ' SUCCESSIVA alla sezione-ancora
    next_h_idx = None
    for i in range(anchor_idx + 1, len(lines)):
        if lines[i].startswith("## "):
            next_h_idx = i
            break
    if next_h_idx is None:
        raise RuntimeError(
            f"nessuna heading '## ' dopo l'ancora '{anchor_prefix}' (punto di inserimento mancante)"
        )

    # 3. inserisci la sezione (col suo separatore '---') prima di next_h_idx,
    #    seguita da una riga vuota che la stacca dalla heading successiva.
    block_lines = build_block(extra_note).split("\n")
    new_lines = lines[:next_h_idx] + block_lines + [""] + lines[next_h_idx:]
    return "\n".join(new_lines), "INIETTATO"


def process(skill_dir: str, anchor_prefix: str, extra_note: str) -> str:
    path = SKILLS_DIR / skill_dir / "SKILL.md"
    if not path.exists():
        return f"ERRORE: {path} non esiste"
    src = path.read_text(encoding="utf-8")
    try:
        new, status = inject(src, anchor_prefix, extra_note)
    except RuntimeError as e:
        return f"ERRORE: {e}"
    if status == "INIETTATO":
        path.write_text(new, encoding="utf-8")
    return status


def main() -> None:
    print(f"inject-orchestration.py — target: {SKILLS_DIR}\n")
    injected = skipped = errors = 0
    for skill_dir, anchor, note in SKILLS:
        status = process(skill_dir, anchor, note)
        tag = "[heavy]" if skill_dir in HEAVY else "[light]"
        print(f"  {skill_dir:22s} {tag:8s} -> {status}")
        if status == "INIETTATO":
            injected += 1
        elif status.startswith("SKIP"):
            skipped += 1
        else:
            errors += 1
    print(f"\nRiepilogo: {injected} iniettate, {skipped} skip (idempotente), {errors} errori.")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
