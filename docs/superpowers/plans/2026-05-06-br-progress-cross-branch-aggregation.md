# BR Progress Cross-Branch Aggregation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix progress visibility across branches by adding cross-branch aggregation to all reader skills and multi-repo branch creation to the executor.

**Architecture:** Three SKILL.md files are modified. A shared aggregation pattern is added to each reader (br-executor for dependency checks, br-pipeline for dashboard, br-progress-report for Excel). The executor also gets multi-repo branch creation and push reminders. No code changes — these are Claude Code skill instruction files.

**Tech Stack:** Git CLI (`git fetch`, `git show`, `git branch -r`), Markdown (SKILL.md format)

**Spec:** `docs/superpowers/specs/2026-05-06-br-progress-cross-branch-aggregation-design.md`

---

### Task 1: br-executor — Aggregazione cross-branch e creazione branch multi-repo

**Files:**
- Modify: `~/.claude/skills/br-executor/SKILL.md`

Tre modifiche allo stesso file: (A) nuova sezione aggregazione + modifica controllo dipendenze, (B) riscrittura creazione branch per multi-repo, (C) aggiornamento suggerimento commit con push reminder e supporto multi-repo.

- [ ] **Step 1: Aggiungere la sezione "Lettura progresso aggregata" prima di "Controllo dipendenze"**

Inserire questa nuova sezione subito prima di `### Controllo dipendenze` (riga 195):

```markdown
### Lettura progresso aggregata (cross-branch)

Prima di leggere il file di progresso per qualsiasi operazione (controllo dipendenze, stato task), esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task, non solo quelle visibili sul branch corrente.

Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch. Senza aggregazione, il progresso degli altri non e' visibile.

1. `git fetch origin` per sincronizzare i branch remoti

2. Leggi il PROGRESSO dal branch base del piano:
   ```bash
   git show origin/<base-branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se il file non esiste sul base branch, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

3. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre gli ID di tutte le task (T-001, T-003, T-005, ...).

4. Cerca i branch remoti corrispondenti alle task del piano:
   ```bash
   git branch -r | grep -E "feature/.*(T-001|T-003|T-005|...)"
   ```
   Usa gli ID task effettivi trovati nel piano.

5. Per ogni branch trovato, leggi il PROGRESSO:
   ```bash
   git show origin/<branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se `git show` fallisce (file non esiste su quel branch), skip.

6. Aggrega per task:
   - Per ogni task nel baseline, cerca la stessa task (match per ID) nelle versioni lette dai feature branch
   - Se nella versione del feature branch la colonna **Branch** coincide con il nome del branch remoto (confronto stringa esatto dopo aver rimosso il prefisso `origin/`, es. `origin/feature/T-001-booking` diventa `feature/T-001-booking`), quella versione e' autoritativa — usala al posto della versione baseline
   - Se nessun feature branch reclama la task, mantieni la versione del baseline

7. Ricalcola le metriche di riepilogo (task completate, in corso, progresso complessivo %) dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning:

> Impossibile sincronizzare con il remoto. Il progresso mostrato potrebbe non essere aggiornato.

Usa la vista aggregata per tutte le operazioni successive (controllo dipendenze, selezione task).
```

- [ ] **Step 2: Modificare "Controllo dipendenze" per usare la vista aggregata**

Sostituire il contenuto attuale della sezione `### Controllo dipendenze` (righe 195-214) con:

```markdown
### Controllo dipendenze

Prima di iniziare una task, verifica le dipendenze usando la **vista aggregata** (vedi sezione "Lettura progresso aggregata" sopra). NON usare il file di progresso locale — potrebbe non riflettere il lavoro completato da altri sviluppatori sui loro branch.

La regola e' semplice: una dipendenza e' soddisfatta quando il suo stato nella vista aggregata e' **"Completata"**. Non serve nessun controllo sugli stream — le dipendenze cross-stream sono gestite tramite merge task esplicite inserite nel piano da br-analyzer.

Logica di verifica per ogni dipendenza:

1. Esegui la lettura progresso aggregata (se non gia' fatta in questa sessione)
2. Trova la task dipendenza nella vista aggregata
3. Verifica che lo stato sia "Completata"
4. Se si', la dipendenza e' soddisfatta — procedi

Se tutte le dipendenze sono soddisfatte, procedi normalmente.

Se una dipendenza non e' soddisfatta, avvisa e blocca:

> La task **T-005** dipende da **T-003**.
> T-003 risulta ancora [stato attuale nella vista aggregata]. Non posso procedere finche' non e' completata.
>
> Vuoi:
> 1. Passare a un'altra task senza dipendenze bloccanti?
> 2. Attendere? (ti chiedero' di controllare il progresso piu' tardi)
```

- [ ] **Step 3: Riscrivere "Creazione branch" per supporto multi-repo**

Sostituire il contenuto attuale della sezione `### Creazione branch` (righe 216-225) con:

```markdown
### Creazione branch

Quando la task e' confermata e le dipendenze sono soddisfatte, crea i branch in TUTTE le repo coinvolte.

1. Identifica le repo coinvolte dalla colonna **Area** del piano (es. BE, FE, BE+FE, EM, DM)
2. **Repo del piano** (la repo corrente, dove stai lavorando):
   - Verifica il branch corrente e lo stato del repository
   - Crea il branch dal base branch del piano:
     > Creo il branch `feature/<task-name>` dal branch `<branch-base>`.
   - Aggiorna il file di progresso con il nome del branch e lo stato "In corso"

3. **Per ogni altra repo coinvolta** (identificata dalla colonna Area e dai path locali forniti in Fase 1):
   - Verifica il branch corrente nella repo esterna:
     ```bash
     git -C <path-repo-esterna> branch --show-current
     ```
   - Crea il feature branch nella repo esterna:
     ```bash
     git -C <path-repo-esterna> checkout -b feature/<task-name>
     ```
   - Comunica al developer:
     > Branch creato anche nella repo **<Nome> (<SIGLA>)**:
     > `feature/<task-name>` da `<branch-corrente>`
     > Path: `<path-repo-esterna>`

4. Se la task riguarda SOLO la repo del piano (es. Area = "BE" e il piano sta in BE), crea un solo branch come al punto 2.
```

- [ ] **Step 4: Aggiornare "Suggerimento commit" con push reminder e supporto multi-repo**

Sostituire il contenuto attuale della sezione `### Suggerimento commit` (righe 299-315) con:

```markdown
### Suggerimento commit

L'agente non deve mai committare autonomamente. Quando il lavoro di un sotto-step e' completo e verificato, avvisa lo sviluppatore con suggerimenti separati per ogni repo coinvolta.

**Se la task coinvolge solo la repo del piano:**

> Il lavoro su [descrizione sotto-step] e' completo e verificato:
> - [lista file creati/modificati]
> - Test: [passano / N test, tutti verdi]
> - Build: [compila]
>
> Sarebbe un buon momento per creare un commit. Suggerisco:
> ```
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> Dopo il commit, pusha il branch per rendere il progresso visibile agli altri:
> ```
> git push origin <nome-branch>
> ```
>
> Quando hai committato e pushato, dimmelo e proseguo.

**Se la task coinvolge piu' repo:**

> Il lavoro su [descrizione sotto-step] e' completo e verificato.
>
> **Repo <Nome Piano> (<SIGLA>)** — `<path-repo-piano>`:
> - [lista file creati/modificati nella repo piano, incluso PROGRESSO_BR.md]
> Suggerisco:
> ```
> git add [file specifici]
> git commit -m "[br-progress] <task-id> -> <progresso>%"
> ```
>
> **Repo <Nome Esterna> (<SIGLA>)** — `<path-repo-esterna>`:
> - [lista file creati/modificati nella repo esterna]
> Suggerisco:
> ```
> cd <path-repo-esterna>
> git add [file specifici]
> git commit -m "feat(<area>): <descrizione concisa>"
> ```
>
> Dopo i commit, pusha entrambi i branch:
> ```
> git push origin <nome-branch>
> cd <path-repo-esterna> && git push origin <nome-branch>
> ```
>
> Quando hai committato e pushato, dimmelo e proseguo.

Aspetta la conferma prima di proseguire con il sotto-step successivo.
```

- [ ] **Step 5: Verificare la coerenza del file**

Leggi l'intero file `~/.claude/skills/br-executor/SKILL.md` e verifica:
- La nuova sezione "Lettura progresso aggregata" appare prima di "Controllo dipendenze"
- "Controllo dipendenze" referenzia la vista aggregata
- "Creazione branch" gestisce multi-repo
- "Suggerimento commit" include il push reminder e il supporto multi-repo
- Nessun conflitto con le altre sezioni del file (Fase 1, Fase 2, Fase 4)

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/br-executor
git add SKILL.md
git commit -m "feat(br-executor): add cross-branch progress aggregation, multi-repo branches, push reminder"
```

Se la directory non e' un repo git, salta il commit — le modifiche sono gia' salvate.

---

### Task 2: br-pipeline — Aggregazione cross-branch per dashboard

**Files:**
- Modify: `~/.claude/skills/br-pipeline/SKILL.md`

- [ ] **Step 1: Aggiungere la sezione "Lettura progresso aggregata" prima di "Dashboard TL/PM"**

Inserire questa nuova sezione nella Fase 2, subito prima di `### Dashboard TL/PM` (riga 88):

```markdown
### Lettura progresso aggregata (cross-branch)

Prima di mostrare la dashboard (sia TL/PM che Dev), esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task. Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch — senza aggregazione si vedrebbe solo il progresso locale.

Per ogni BR con `stato_pipeline` uguale a `"execute"` o `"approved"`:

1. `git fetch origin` per sincronizzare i branch remoti

2. Trova la cartella del BR in `plans/`: `plans/*/YYYY-*_<nome>/`

3. Leggi il PROGRESSO dal branch base del piano:
   ```bash
   git show origin/<base-branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se il file non esiste sul base branch, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

4. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre gli ID di tutte le task (T-001, T-003, T-005, ...).

5. Cerca i branch remoti corrispondenti alle task del piano:
   ```bash
   git branch -r | grep -E "feature/.*(T-001|T-003|T-005|...)"
   ```
   Usa gli ID task effettivi trovati nel piano.

6. Per ogni branch trovato, leggi il PROGRESSO:
   ```bash
   git show origin/<branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se `git show` fallisce (file non esiste su quel branch), skip.

7. Aggrega per task:
   - Per ogni task nel baseline, cerca la stessa task (match per ID) nelle versioni lette dai feature branch
   - Se nella versione del feature branch la colonna **Branch** coincide con il nome del branch remoto (confronto stringa esatto dopo aver rimosso il prefisso `origin/`), quella versione e' autoritativa — usala al posto della versione baseline
   - Se nessun feature branch reclama la task, mantieni la versione del baseline

8. Ricalcola le metriche di riepilogo (task completate, in corso, progresso complessivo %) dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning:

> Impossibile sincronizzare con il remoto. Il progresso mostrato potrebbe non essere aggiornato.

Usa la vista aggregata per tutte le operazioni successive in questa fase.
```

- [ ] **Step 2: Modificare "Dashboard TL/PM" per usare la vista aggregata**

Nella sezione `### Dashboard TL/PM`, dopo la tabella dei BR e prima di "Azioni suggerite", modificare il testo dei BR in stato `execute` per indicare che il progresso viene dalla vista aggregata.

Sostituire (riga 109-111):

```markdown
> **booking-v3** (`execute`):
> 3/10 task completate. Progresso: 30%.
> → Vuoi vedere il dettaglio delle task? Oppure generare l'Excel di avanzamento?
```

Con:

```markdown
> **booking-v3** (`execute`):
> 3/10 task completate. Progresso: 30%. *(aggregato da N branch remoti)*
> → Vuoi vedere il dettaglio delle task? Oppure generare l'Excel di avanzamento?
```

- [ ] **Step 3: Modificare "Dashboard Dev" per usare la vista aggregata**

Nella sezione `### Dashboard Dev`, sostituire la riga che descrive come trovare le task (riga 148):

```markdown
Trova tutti i BR con `stato_pipeline: "execute"` o `"approved"` e `piano.approvato: true`. Per ognuno, cerca le task assegnate al developer nel `PIANO_IMPLEMENTAZIONE_BR.md` e nel `PROGRESSO_BR.md` nella cartella `plans/`.
```

Con:

```markdown
Trova tutti i BR con `stato_pipeline: "execute"` o `"approved"` e `piano.approvato: true`. Per ognuno, esegui la **lettura progresso aggregata** (vedi sezione sopra) e filtra le task assegnate al developer dalla vista aggregata.
```

- [ ] **Step 4: Verificare la coerenza del file**

Leggi l'intero file `~/.claude/skills/br-pipeline/SKILL.md` e verifica:
- La sezione "Lettura progresso aggregata" appare nella Fase 2, prima delle dashboard
- Le dashboard TL/PM e Dev referenziano la vista aggregata
- Nessun conflitto con le altre fasi del file (Fase 1, Fase 3-6)

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/br-pipeline
git add SKILL.md
git commit -m "feat(br-pipeline): add cross-branch progress aggregation for dashboard"
```

Se la directory non e' un repo git, salta il commit.

---

### Task 3: br-progress-report — Aggregazione cross-branch per estrazione dati Excel

**Files:**
- Modify: `~/.claude/skills/br-progress-report/SKILL.md`

- [ ] **Step 1: Aggiungere l'aggregazione alla "Fase 2 — Estrazione Dati"**

Sostituire l'inizio della sezione `## Fase 2 — Estrazione Dati` (righe 71-91) con:

```markdown
## Fase 2 — Estrazione Dati

### Lettura progresso aggregata (cross-branch)

Prima di estrarre i dati, esegui l'aggregazione dai branch remoti per ottenere una vista aggiornata del progresso di TUTTE le task. Questo e' necessario perche' ogni sviluppatore aggiorna il PROGRESSO sul proprio feature branch — senza aggregazione l'Excel mostrerebbe solo il progresso locale.

1. `git fetch origin` per sincronizzare i branch remoti

2. Leggi il PROGRESSO dal branch base del piano:
   ```bash
   git show origin/<base-branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se il file non esiste sul base branch, genera un baseline dal PIANO: tutte le task a 0%, stato "Da iniziare".

3. Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre gli ID di tutte le task (T-001, T-003, T-005, ...).

4. Cerca i branch remoti corrispondenti alle task del piano:
   ```bash
   git branch -r | grep -E "feature/.*(T-001|T-003|T-005|...)"
   ```
   Usa gli ID task effettivi trovati nel piano.

5. Per ogni branch trovato, leggi il PROGRESSO:
   ```bash
   git show origin/<branch>:<path-cartella-br>/PROGRESSO_BR.md
   ```
   Se `git show` fallisce (file non esiste su quel branch), skip.

6. Aggrega per task:
   - Per ogni task nel baseline, cerca la stessa task (match per ID) nelle versioni lette dai feature branch
   - Se nella versione del feature branch la colonna **Branch** coincide con il nome del branch remoto (confronto stringa esatto dopo aver rimosso il prefisso `origin/`), quella versione e' autoritativa — usala al posto della versione baseline
   - Se nessun feature branch reclama la task, mantieni la versione del baseline

7. Ricalcola le metriche di riepilogo dalla vista aggregata.

**Fallback**: se `git fetch` fallisce (no rete), usa il file di progresso locale e mostra un warning all'utente.

### Estrazione campi

Dalla vista aggregata e dal piano, estrai per ogni task:

| Campo | Fonte |
|---|---|
| ID | Piano — colonna ID |
| Attivita' | Piano — colonna Attivita' |
| Descrizione | Piano — colonna Descrizione (testo completo) |
| Owner | Piano — colonna Owner |
| Area | Piano — colonna Area (BE/FE) |
| Priorita' | Piano — colonna Priorita' (P0/P1/P2) |
| Wave | Piano — sezione Ordine di esecuzione |
| Dipendenze | Piano — colonna Dipendenze |
| Effort stimato | Piano — colonna Effort |
| Branch | Vista aggregata — colonna Branch |
| Progresso % | Vista aggregata — colonna Progresso |
| Stato | Vista aggregata — colonna Stato (Da iniziare / In corso / Completata / Bloccata / Annullata / Sospesa) |
| Note | Vista aggregata — colonna Note |

Se il file di progresso non esiste e l'aggregazione non trova nessun branch remoto, imposta progresso a 0% e stato a "Da iniziare" per tutte le task.
```

- [ ] **Step 2: Aggiungere info aggregazione al foglio "Riepilogo" dell'Excel**

Nella sezione `### Foglio 3 — "Riepilogo"`, dopo la riga `Ultimo aggiornamento progresso: [data dal file progresso]`, aggiungere:

```markdown
Dati aggregati da: [N] branch remoti
Ultimo fetch: [data e ora del git fetch]
```

Il blocco aggiornato diventa:

```
Progetto: [nome BR]
Data generazione: [data]
Ultimo aggiornamento progresso: [data dal file progresso]
Dati aggregati da: [N] branch remoti
Ultimo fetch: [data e ora del git fetch]
```

- [ ] **Step 3: Verificare la coerenza del file**

Leggi l'intero file `~/.claude/skills/br-progress-report/SKILL.md` e verifica:
- La Fase 2 include la sezione "Lettura progresso aggregata" prima dell'estrazione campi
- La tabella dei campi referenzia "Vista aggregata" per Branch, Progresso, Stato e Note
- Il foglio "Riepilogo" include le info di aggregazione
- Nessun conflitto con le altre fasi del file (Fase 1, Fase 3, Fase 4)

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills/br-progress-report
git add SKILL.md
git commit -m "feat(br-progress-report): add cross-branch progress aggregation for Excel data extraction"
```

Se la directory non e' un repo git, salta il commit.

---

### Task 4: Commit del piano e dello spec nel repo del progetto

**Files:**
- Already created: `docs/superpowers/specs/2026-05-06-br-progress-cross-branch-aggregation-design.md`
- Already created: `docs/superpowers/plans/2026-05-06-br-progress-cross-branch-aggregation.md`

- [ ] **Step 1: Commit spec e piano**

```bash
cd ~/Documents/MyGitHub/claude-flow
git add docs/superpowers/specs/2026-05-06-br-progress-cross-branch-aggregation-design.md
git add docs/superpowers/plans/2026-05-06-br-progress-cross-branch-aggregation.md
git commit -m "docs: add cross-branch progress aggregation design spec and implementation plan"
```
