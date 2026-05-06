# BR Progress Cross-Branch Aggregation — Design Spec

Data: 2026-05-06

## Problema

L'executor aggiorna il file PROGRESSO_BR.md sul proprio feature branch. Ogni developer lavora su un feature branch separato. Il risultato: nessuno vede il progresso degli altri finche' i branch non vengono mergiati. Il TL/PM che controlla la dashboard vede tutto a 0%. Il developer che controlla le dipendenze non sa se la task di un collega e' completata.

## Soluzione

Aggregazione cross-branch lato reader. Le skill che LEGGONO il progresso (br-pipeline, br-progress-report, br-executor per il check dipendenze) non leggono piu' solo il file locale. Invece:

1. Fanno `git fetch origin` per sincronizzare
2. Leggono il PROGRESSO dal branch base del piano (baseline)
3. Identificano i feature branch remoti delle task dal piano
4. Leggono il PROGRESSO da ciascun feature branch via `git show`
5. Aggregano per task: ogni branch e' autoritativo per le task che ci stanno lavorando sopra

Il developer non cambia nulla nel suo workflow. L'unico requisito e' che pushi il feature branch — cosa che fa gia' per le PR.

---

## Architettura

### Flusso attuale (problema)

```
Dev A (feature/T-001) → aggiorna PROGRESSO → commit/push sul feature branch
Dev B (feature/T-003) → aggiorna PROGRESSO → commit/push sul feature branch
TL/PM (base branch)   → legge PROGRESSO   → vede tutto a 0%  ← PROBLEMA
```

### Flusso proposto

```
Dev A (feature/T-001) → aggiorna PROGRESSO → commit/push sul feature branch
Dev B (feature/T-003) → aggiorna PROGRESSO → commit/push sul feature branch
TL/PM (base branch)   → git fetch
                       → legge PROGRESSO da base branch (baseline)
                       → legge PROGRESSO da origin/feature/T-001
                       → legge PROGRESSO da origin/feature/T-003
                       → aggrega per task → vede il progresso reale
```

### Invarianti

- Il PROGRESSO viene SCRITTO esattamente come oggi (sul feature branch). Nessun cambiamento lato scrittura.
- Il PROGRESSO viene LETTO con aggregazione cross-branch. Cambia solo il lato lettura.
- L'aggregazione avviene nella repo dove sta il piano (dove l'executor viene invocato).
- I branch nelle repo esterne (FE, EM, DM) servono per il codice, non per il tracking del progresso.

---

## Algoritmo di Aggregazione

### Step 1 — Sync remoti

```bash
git fetch origin
```

### Step 2 — Leggi il baseline dal branch base del piano

```bash
git show origin/<base-branch>:plans/in-progress/<br>/PROGRESSO_BR.md
```

Se il file non esiste sul base branch, genera un baseline virtuale dal PIANO: tutte le task a 0%, stato "Da iniziare".

### Step 3 — Identifica i branch delle task dal piano

Leggi il PIANO_IMPLEMENTAZIONE_BR.md per estrarre gli ID task (T-001, T-003, T-005, ...). Cerca solo i branch remoti corrispondenti:

```bash
git branch -r | grep -E "feature/.*(T-001|T-003|T-005|T-007)"
```

Niente scansione di tutti i feature branch — solo quelli che corrispondono alle task del piano.

### Step 4 — Leggi PROGRESSO da ogni feature branch trovato

Per ogni branch trovato:

```bash
git show origin/feature/T-001-booking-entity:plans/in-progress/<br>/PROGRESSO_BR.md
```

Se `git show` fallisce (file non esiste su quel branch), skip.

### Step 5 — Aggrega per task

Per ogni task nel baseline:

1. Scansiona tutti i PROGRESSO letti dai feature branch
2. Cerca la task corrispondente (match per ID, es. T-001)
3. Se nella versione del feature branch la colonna **Branch** coincide con il nome del branch remoto (confronto stringa esatto dopo aver rimosso il prefisso `origin/`, es. `origin/feature/T-001-booking` → `feature/T-001-booking`) → quella versione e' autoritativa, usala
4. Se nessun feature branch reclama la task → resta la versione del baseline

### Esempio

```
Baseline (origin/develop):
| T-001 | Booking entity | Marco  | 0%  | Da iniziare | —                            |
| T-003 | Repository     | Marco  | 0%  | Da iniziare | —                            |
| T-005 | Componente FE  | Luca   | 0%  | Da iniziare | —                            |

origin/feature/T-001-booking-entity:
| T-001 | Booking entity | Marco  | 80% | In corso    | feature/T-001-booking-entity |  ← match!
| T-003 | Repository     | Marco  | 0%  | Da iniziare | —                            |  ← stale, ignora
| T-005 | Componente FE  | Luca   | 0%  | Da iniziare | —                            |  ← stale, ignora

origin/feature/T-005-componente-fe:
| T-001 | Booking entity | Marco  | 0%  | Da iniziare | —                            |  ← stale, ignora
| T-003 | Repository     | Marco  | 0%  | Da iniziare | —                            |  ← stale, ignora
| T-005 | Componente FE  | Luca   | 40% | In corso    | feature/T-005-componente-fe  |  ← match!

Vista aggregata (costruita dal reader):
| T-001 | Booking entity | Marco  | 80% | In corso    | feature/T-001-booking-entity |
| T-003 | Repository     | Marco  | 0%  | Da iniziare | —                            |
| T-005 | Componente FE  | Luca   | 40% | In corso    | feature/T-005-componente-fe  |
```

### Ricalcolo metriche

Dopo l'aggregazione, il reader ricalcola il riepilogo (task completate, in corso, progresso complessivo %) dalla vista aggregata, non dal baseline.

---

## Skill Impattate

### br-executor — Modifica 1: Controllo dipendenze

Sezione "Fase 3 — Controllo dipendenze". Oggi verifica le dipendenze dal file locale. Con l'aggregazione:

Prima di verificare le dipendenze:

1. `git fetch origin`
2. Leggi il PIANO per estrarre gli ID task
3. `git branch -r | grep -E "feature/.*(T-001|T-003|...)"` per trovare i branch attivi
4. Per ogni branch trovato, `git show origin/<branch>:<path-progresso>`
5. Aggrega: per ogni task, se la colonna Branch coincide con il branch remoto, usa quella versione
6. Verifica le dipendenze sulla vista aggregata, non sul file locale

### br-executor — Modifica 2: Suggerimento push

Sezione "Fase 3 — Suggerimento commit". Dopo ogni suggerimento di commit che include aggiornamenti al PROGRESSO, aggiungere:

> Dopo il commit, pusha il branch per rendere il progresso visibile agli altri:
> `git push origin <nome-branch>`

### br-executor — Modifica 3: Creazione branch multi-repo

Sezione "Fase 3 — Creazione branch". L'executor identifica TUTTE le repo coinvolte nella task (dalla colonna Area del piano) e crea il feature branch in ognuna.

Flusso per una task FE-only, executor invocato dalla repo BE (piano):

```
1. Executor legge Area = "FE" dal piano
2. Repo del piano (BE):
   - git checkout -b feature/T-005-componente-fe
   - Aggiorna PROGRESSO → stato "In corso", Branch = "feature/T-005-componente-fe"
3. Repo FE (codice):
   - Verifica il branch corrente: git -C <path-FE> branch --show-current
   - Crea il branch: git -C <path-FE> checkout -b feature/T-005-componente-fe
   - Comunica al developer quale branch e' stato creato e da dove
4. Sottoagenti lavorano nella repo FE sul branch corretto
```

Flusso per una task BE+FE:

```
1. Executor legge Area = "BE+FE" dal piano
2. Repo BE: git checkout -b feature/T-010-fullstack → tracking + codice BE
3. Repo FE: git -C <path-FE> checkout -b feature/T-010-fullstack → codice FE
4. Sottoagenti lavorano in entrambe le repo sui branch corretti
```

Suggerimento commit multi-repo:

```
> Repo BE (plans/):
> - plans/in-progress/.../PROGRESSO_BR.md (aggiornato)
> Suggerisco: git add plans/... && git commit -m "[br-progress] T-005 → 40%"
>
> Repo FE (<path-FE>):
> - src/components/MonitoringTable.tsx (creato)
> Suggerisco: cd <path-FE> && git add src/... && git commit -m "feat(monitoring): add table component"
>
> Dopo i commit, pusha entrambi i branch:
> git push origin feature/T-005-componente-fe
> cd <path-FE> && git push origin feature/T-005-componente-fe
```

### br-pipeline — Lettura progresso per la dashboard

Sezione "Fase 2 — Dashboard TL/PM" e "Dashboard Dev". Prima di mostrare la dashboard, la pipeline esegue l'aggregazione cross-branch con la stessa logica dell'executor. La dashboard TL/PM e la dashboard Dev usano entrambe la vista aggregata; cambia solo il filtro (TL/PM vede tutto, Dev vede solo le proprie task).

### br-progress-report — Estrazione dati per Excel

Sezione "Fase 2 — Estrazione Dati". Prima dell'estrazione dati, eseguire l'aggregazione cross-branch. L'Excel viene generato dalla vista aggregata. Aggiungere nel foglio "Riepilogo":

```
Dati aggregati da N branch remoti
Ultimo fetch: <timestamp>
```

---

## Edge Case

| # | Scenario | Gestione |
|---|---|---|
| 1 | Dev non ha pushato il feature branch | Reader usa la versione del baseline (0%). L'executor mitiga con il reminder di push. |
| 2 | Feature branch mergiato e cancellato | Il merge ha portato gli aggiornamenti nel base branch. Il baseline e' gia' aggiornato. |
| 3 | `git fetch` fallisce (no rete) | Fallback: usa il file locale. Warning: "Progresso potrebbe non essere aggiornato." |
| 4 | Task torna indietro (In corso → Bloccata) | Il match e' sulla colonna Branch, non sul valore. Il branch autoritativo vince con qualsiasi stato. |
| 5 | Merge task (T-MERGE-\*) | Nessun feature branch proprio. Resta la versione del baseline. Aggiornata sul base branch al merge. |
| 6 | PROGRESSO non esiste sul base branch | Genera un baseline virtuale dal PIANO: tutte le task a 0%, "Da iniziare". |
| 7 | Branch abbandonato (creato, mai lavorato) | La colonna Branch e' "—" → nessun match. Reader usa il baseline. |
| 8 | Due branch reclamano la stessa task | Usa il timestamp "Ultimo aggiornamento" piu' recente. |

---

## Impatto sul Workflow del Developer

### Workflow dopo il cambiamento

```
1. Dev avvia br-executor dalla repo del piano
2. Seleziona la task
3. Executor crea feature branch nella repo del piano (tracking)
4. Executor crea feature branch nelle repo coinvolte (codice)     ← NUOVO
5. Sottoagenti implementano codice e test nelle repo target
6. Executor suggerisce commit separati per repo               ← NUOVO
7. Executor suggerisce push per rendere il progresso visibile  ← NUOVO
8. Ripete 5-7 fino al completamento della task
9. Dev fa la PR / merge quando ha finito
```

### Cosa NON cambia

- Il formato di PROGRESSO_BR.md resta identico
- L'executor scrive PROGRESSO esattamente come oggi (sul feature branch nella repo del piano)
- Le merge task funzionano come oggi
- Claude non committa e non pusha mai
- La retrocompatibilita' con file flat e' preservata
- Il developer non deve mai switchare branch per aggiornare il progresso

### Conflitti

- **Push**: nessuno. Ogni dev pusha solo sul proprio feature branch.
- **Merge**: possibili su PROGRESSO al merge del feature branch, ma irrilevanti — il reader aggrega dai branch, non dipende dalla versione sul base branch. Il dev puo' accettare qualsiasi versione al merge.

---

## Vincoli e Prerequisiti

| Vincolo | Descrizione |
|---|---|
| Executor invocato dalla repo del piano | L'executor cerca `plans/` nella working directory. Deve essere invocato dalla repo dove il piano e' stato creato. |
| Tutti i dev hanno tutte le repo | Ogni developer ha un clone locale di tutte le repo coinvolte nel BR. |
| Push del feature branch | Il progresso diventa visibile solo dopo il push. Non e' obbligatorio ma e' il meccanismo di sync. |
| Naming dei branch | I branch devono contenere l'ID della task (es. `feature/T-001-booking-entity`). L'executor gia' lo fa. |
| Connessione di rete | `git fetch` richiede accesso al remote. Senza rete, fallback al file locale. |
