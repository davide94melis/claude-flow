# Changelog globale per progetto — write-contract condiviso (miglioria #3)

> Riferimento condiviso (SoT: `skills/sdlc-executor/references/`, rispecchiato byte-identico nel plugin). Definisce **formato**, **posizione**, **contratto di scrittura** e **convenzione di lettura** del changelog globale `CHANGELOG.md`. Tutte le skill che scrivono/leggono lo storico cross-piano seguono questo contratto. Helper: `${SCRIPTS}/changelog.py` (stdlib, grep-compatibile, **niente jq**).

---

## 1. Cos'è e cosa NON è

`CHANGELOG.md` = **storia append-only cross-piano** dei lavori completati su un'app/progetto, con puntatori (commit-ref + jump ai PROGRESS). È il punto unico, sintetico e sempre aggiornato di "cosa è stato fatto".

Boundary (nessuna duplicazione):
- `PROGRESS.md` = stato **corrente** per-piano (fonte di verità del piano).
- `progress-report` (Excel) = dashboard stato **per-dev**.
- **`CHANGELOG.md` = storia append-only cross-piano** con puntatori.

## 2. Posizione e bootstrap

- **Path:** `CHANGELOG.md` alla **root della repo specifiche/profilo** (un changelog per progetto). Risoluzione robusta: `PROJECT_ROOT="$(dirname "$BASE_PATH")"` → `CHANGELOG_PATH="$PROJECT_ROOT/CHANGELOG.md"` (sibling di `plans/`; vale sia standalone sia legacy `<profiles-repo>/<profilo>/`).
- **Bootstrap:** se assente, il **primo writer** lo crea con `changelog.py init --file "$CHANGELOG_PATH" --project "<PROJECT_NAME>"` (no-op se esiste).
- **Backfill opzionale una-tantum:** all'avvio l'executor può popolare l'indice `## Piani` dai piani già in `done/`/`in-progress/` (dai loro PROGRESS) con `upsert-plan` per ciascuno — **senza** feed retroattivo per-task.
- **Manutenzione path indice:** quando un piano cambia stato (`todo→in-progress→done`) il path del suo PROGRESS cambia → ri-esegui `upsert-plan` per aggiornare la riga.

## 3. Formato (human-first + machine-anchored)

```markdown
# Changelog — <app/progetto>
> Synthetic cross-plan index. Auto-updated by sdlc-executor (+ shared write-contract). Append-only.
> For details follow the PROGRESS / commit links.

## Piani
| Plan | Status | Period | Tasks done/tot | PROGRESS | Summary (1 line) |
|---|---|---|---|---|---|
| 2026-07-20_registrazione | in-progress | 2026-07-18→ | 3/8 | plans/in-progress/2026-07-20_registrazione/PROGRESS.md | PL registration + 2FA |

## Attività (recent → old)
### 2026-07-20
- **T-003** [BE] Monitoring-practice list repository — *plan: 2026-07-20_registrazione* — commit: `BE@1a2b3c4` — → PROGRESS#T-003
### 2026-07-19
- **✔ PLAN DONE** 2026-07-15_booking-v2 — 12/12 tasks, 0 open bugs — commit range `BE@aaa..bbb`, `FE@ccc..ddd` — → PROGRESS
```

- **Voce task:** `data · **T-ID** · [area/SIGLA] · sintesi 1-riga · plan · commit(SIGLA@sha, N) · → PROGRESS#ancora`.
- **Entry piano completato:** `**✔ PLAN DONE** <plan> — done/tot tasks, N open bugs — commit range — → PROGRESS`.
- Feed **newest-first**; raggruppato per data (`### YYYY-MM-DD`). Gli anchor stabili (`## Piani`, `## Attività`, `|---|`) permettono il grep read-first senza parsing fragile.

## 4. Cattura commit-ref (rispetta l'invariante "mai auto-commit sul codice")

L'executor **non committa** sul codice, ma **legge** (read-only). Dopo che il dev ha committato+pushato e confermato:

```bash
# per ogni repo di codice della task, i commit nuovi dalla base al branch della task
git -C "<repo-codice>" log --pretty=%h "<branch-base>..<branch-task>"
```

Registra gli **short-SHA** per repo come `<SIGLA>@<sha>` nella voce. Per il piano completato calcola il **range** `base..head` per repo. Nessuna scrittura sul codice.

## 5. Contratto di scrittura (write-contract — chi scrive cosa)

| Writer | Evento → voce | Comando |
|---|---|---|
| **sdlc-executor** | task completata | `changelog.py task --file $CL --date <D> --id <T-ID> --area <SIGLA> --summary "..." --plan <plan> --commits "<SIGLA@sha,...>" --progress <progress-rel>` |
| **sdlc-executor** | piano completato | `changelog.py plan-done --file $CL --date <D> --plan <plan> --done <N> --tot <M> --bugs <K> --range "<SIGLA@base..head,...>" --progress <progress-rel>` |
| **sdlc-executor** | spostamento stato | `changelog.py upsert-plan --file $CL --plan <plan> --status <s> --period <p> --tasks "<d>/<t>" --progress <progress-rel> --summary "..."` |
| **sdlc-debug** | bug chiuso | `changelog.py add-activity --file $CL --date <D> --line "[BUG] <id> fixed — *plan: <plan>* — commit: \`<SIGLA@sha>\` — → PROGRESS"` |
| **sdlc-updater** | delta piano/AFU | `changelog.py add-activity --file $CL --date <D> --line "[UPDATE] <plan> scope changed — <sintesi>"` |
| **sdlc-merge (#2)** | piani mergiati | `changelog.py add-activity --file $CL --date <D> --line "⇄ MERGE <plans> — commit: \`<SIGLA@sha>\` — → INTEGRATION"` |
| **sdlc-verifier (#4)** | task iniettate | `changelog.py add-activity --file $CL --date <D> --line "[VERIFY] +<N> task in <plan> — → VERIFICATION"` |

> MVP di #3: cablati **executor** (create/backfill + task/plan/moves + cattura SHA) e questo file/helper. Gli hook di **sdlc-merge (#2)** e **sdlc-verifier (#4)** sono cablati nelle rispettive skill (stesso helper). Gli hook di **debug**/**updater** sono un follow-up leggero (stesso helper, stessa disciplina).

## 6. Disciplina di scrittura (single-writer serializzato)

Ogni scrittura sul changelog segue la **stessa disciplina del PROGRESS** sulla repo specifiche/profilo:

```bash
git -C "$GIT_REPO_PATH" pull origin main --quiet
python "${SCRIPTS}/changelog.py" <sottocomando> --file "$CHANGELOG_PATH" ...
git -C "$GIT_REPO_PATH" add "$CHANGELOG_PATH"
git -C "$GIT_REPO_PATH" commit -m "[sdlc-changelog] <evento>"
git -C "$GIT_REPO_PATH" push origin main --quiet
```

Invarianti: **mai auto-commit sul codice**; single-writer serializzato sulla repo specifiche/profilo; helper idempotente (doppio append della stessa voce = no-op); `${SCRIPTS}` = `${CLAUDE_PLUGIN_ROOT}/scripts` (plugin) o `<claude-flow>/scripts` (SoT).

## 7. Convenzione di lettura ("read first")

All'avvio, **dopo il `git pull`** e **prima** di aprire i file per-piano, le skill leggono `CHANGELOG.md` per storia + jump-point:

| Reader | Uso |
|---|---|
| **sdlc-analyzer** | cosa è già stato fatto (evita ri-pianificare lavoro done; consapevolezza impatto) |
| **sdlc-updater** | contesto delta (cosa è cambiato di recente) |
| **sdlc-verifier (#4)** | cosa è stato implementato per piano + jump ai PROGRESS |
| **sdlc-merge (#2)** | cosa ha prodotto ogni piano + commit-ref da mergiare |
| **sdlc-debug** | contesto sulle modifiche recenti |
| **sdlc-progress-report** | cross-check storico (non sostituisce l'aggregazione) |

Lettura grep-compatibile (niente jq), es.:

```bash
[ -f "$CHANGELOG_PATH" ] && sed -n '/^## Piani/,/^## Attività/p' "$CHANGELOG_PATH"   # indice piani
[ -f "$CHANGELOG_PATH" ] && grep -A3 '^## Attività' "$CHANGELOG_PATH"                 # ultime attività
```

## 8. Lingua

Il changelog è **solo EN** (dev-facing, coerente con PROGRESS/TASKS/commit). La sintesi 1-riga è concisa in EN.
