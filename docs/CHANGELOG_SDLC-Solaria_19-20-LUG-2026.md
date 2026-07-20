# Changelog SDLC & Solaria — 19-20 Luglio 2026

Riepilogo di tutto ciò che è stato portato su `main` in queste giornate, su **due repository**:
`claude-flow` (dove vivono le skill SDLC) e il marketplace (dove vivono gli agenti Solaria e
la copia pubblicata delle skill come plugin `sdlc-suite`).

Il lavoro è diviso in due gruppi:

1. **Feedback round** — 9 migliorie nate da feedback d'uso reale sul campo.
2. **Follow-up round** — 3 rifiniture finali che chiudono i punti rimasti aperti dal feedback round.

Entrambe le parti coprono **sia le skill SDLC** (le 9 skill che guidano il ciclo
analisi → sviluppo → test) **sia gli agenti Solaria** (i 6 agenti che generano il documento
funzionale a monte).

### Glossario rapido (per leggere senza sigle)

| Sigla | Significato |
|---|---|
| **AFU** | Analisi Funzionale Utente — il documento funzionale di input (in passato chiamato "BR"). |
| **Skill SDLC** | Le 9 skill: analyzer, reviewer, clarify, updater, executor, debug, estimator, profile-setup, progress-report. |
| **Agenti Solaria** | I 6 agenti che scrivono l'AFU: Orchestrator (00), Weaver (01), Reviewer (02), Mockup Designer (03), Playbook Generator (04), Accessibility Assistant (05). |
| **Piano / TASKS / PLAN** | Il piano di implementazione generato dall'analyzer a partire dall'AFU. |
| **Dev-facing** | Artefatti per gli sviluppatori (gap report, piano, task, progresso, commit). |
| **Funzionale/end-user** | Artefatti per il funzionale/utente (AFU, chiarimenti, playbook di test, report accessibilità). |
| **SoT** (source of truth) | La copia "sorgente" da cui le altre vengono allineate: per le skill è `claude-flow`, rispecchiata **byte per byte** nel plugin `sdlc-suite`. |

---

## Numeri complessivi

| Metrica | Valore |
|---|---|
| Repository coinvolti | 2 (claude-flow, marketplace) |
| Pull request mergiate | 4 |
| Skill SDLC toccate | 9 (tutte) |
| Agenti Solaria toccati | 6 (tutti) + contratto/schema |
| File nuovi | template AFU in inglese; schema/fixture del gate; esempi contratto |
| Verifica qualità | review avversariale sul follow-up (5 problemi trovati, tutti risolti); parità byte-identica skill↔plugin |

---

## Parte 1 — Cosa è cambiato nelle SKILL SDLC

### 1. Le skill trovano il progetto anche dalla cartella "contenitore"
Prima una skill leggeva la configurazione (`.sdlc-local.json`) **solo** nella cartella corrente.
Ora, se apri Claude sulla cartella che *contiene* i progetti, la skill cerca la configurazione
nelle sottocartelle, deduplica per progetto e — se ne trova più d'uno diverso — **chiede quale
usare** invece di sbagliare silenziosamente. (Applicato a tutte e 9 le skill.)

### 2. Lingua di interazione IT/EN e regola per tipo di documento
Nuovo campo `interaction_language` (`it` o `en`): se manca, la skill **lo chiede una volta e lo
salva** (nessun default silenzioso). Regola su quale lingua produrre gli artefatti:
- **Documenti per gli sviluppatori** (gap report, piano, task, progresso, commit) → **solo inglese**.
- **Documenti per il funzionale/utente** (AFU, chiarimenti, playbook) → **lingua scelta + copia in
  inglese affiancata** (file `<nome>.en.<estensione>`).
- **Mockup** → solo lingua utente (nessuna copia inglese).

### 3. Modalità di scomposizione del piano (analyzer)
Quando l'analyzer spezza l'AFU in task, ora **chiede** come bilanciare:
- **Testabilità prima** (default) — task più grandi ma verificabili in isolamento.
- **Parallelizzazione prima** — task più piccole e parallele, con più task di merge.

Il default può essere pre-impostato nel profilo di progetto.

### 4. Scadenza e cadenza di avanzamento (analyzer + progress-report)
L'analyzer può registrare **data di inizio e deadline** nell'intestazione del piano. Il report di
avanzamento calcola la **cadenza necessaria** (giorni-uomo al giorno, e task al giorno) e mostra un
blocco **ANTICIPO / RITARDO** rispetto alla previsione lineare.

### 5. Corretto il bug dell'avanzamento a 0% (progress-report)
Prima, se il recupero dei dati da `main` falliva, il report poteva **azzerare** i progressi. Ora:
il recupero è **verificato** (se fallisce, si ferma con un messaggio chiaro), la lettura avviene
direttamente da `origin/main`, e una **guardia** impedisce di sovrascrivere un report valido con
tutti zero. Il vecchio script `aggregate-progress.py` è deprecato.

### 6. Template Excel di avanzamento personalizzato (progress-report + profile-setup)
Il Team Leader può fornire un **proprio `.xlsx`**: la skill lo analizza in un "manifest" (fogli,
colonne, formattazione), mostra l'interpretazione, permette di correggerla e — a conferma — la
**salva nel profilo di progetto**. Da lì in poi il report viene generato con quel layout. Aggiunto
uno script di rendering committato (`generate-progress-xlsx.py`).

### 7. Allineamento automatico dei repository prima di lavorare una task (executor)
Quando una task **usa** il lavoro di una dipendenza già completata che vive su un altro repository,
l'executor esegue un **preflight**: costruisce la mappa repo → branch, controlla che l'albero di
lavoro sia pulito (mai `--force`), fa `fetch` e allinea i repository "consumati" al branch giusto
(solo fast-forward, con conferma). È un no-op se il progetto ha un solo repository.

### 8. Contratto API tra Frontend e Backend definito prima (analyzer + executor + updater)
Quando un requisito richiede un'API tra FE e BE, l'analyzer genera una **task-contratto prioritaria**
(prima wave) che scrive e "congela" il contratto in `CONTRACTS.md` (endpoint, schemi
request/response, codici errore, auth). Le task FE e BE **dipendono** da quella e ne **citano l'ID**;
la wave finale diventa un semplice controllo di conformità invece di una riconciliazione a posteriori.
L'updater tiene traccia delle modifiche al contratto.

### 9. (Follow-up) Nomi di branch diversi per repository (analyzer + executor)
Prima si assumeva **lo stesso nome di branch** su tutti i repository di una task. Ora, se un progetto
usa nomi diversi, si possono indicare nella colonna Branch con il formato `SIGLA:branch` (es.
`BE:feature/x-be; FE:feature/x-fe`); un nome "nudo" continua a valere per tutti. L'executor risolve
il branch **per singolo repository** in tutti i punti (allineamento, creazione branch, push).

---

## Parte 2 — Cosa è cambiato negli AGENTI SOLARIA

### 1. AFU scritta in linguaggio funzionale, non tecnico (Weaver 01 + Reviewer 02)
Il Weaver (che scrive l'AFU) ora ha una **lista di divieti espliciti**: niente nomi fisici di
tabelle/colonne/database, classi/service/DTO, rotte o verbi HTTP, framework, path di file o chiavi
di configurazione. Deve **tradurre** il contesto tecnico del brownfield in linguaggio funzionale.
Il Reviewer (che valuta l'AFU) ha una nuova dimensione di qualità **"agnosticism"** (punteggio
0-100, solo informativa) con schema e casi di test pass/fail.

### 2. Lingua gestita dall'Orchestrator e propagata a tutti (Orchestrator 00 + worker 01-05)
L'Orchestrator chiede **una volta** la lingua di interazione e la propaga a tutti i sotto-agenti.
Regola per tipo di artefatto: AFU, chiarimenti e playbook sono **duali** (lingua scelta + copia
`.en`); i **mockup** sono in una sola lingua (quella utente); lo schema/gate del Reviewer resta
neutro. Tutti i worker sono stati riscritti di conseguenza e i **6 file JSON** degli agenti
rigenerati dal sorgente.

### 3. (Follow-up) Template dell'AFU disponibile anche in inglese (Weaver 01 + contratto)
Poiché l'AFU va prodotta anche in copia inglese, prima mancava una **struttura di riferimento in
inglese** da seguire. Aggiunto `afu-feature-first-template.en.md`, copia inglese del template (stessa
struttura, stessi identificatori); il Weaver ora lo usa per la copia `AFU-<slug>.en.md`.

### 4. (Follow-up) Report di accessibilità salvabile come artefatto (Orchestrator 00, Mockup Designer 03, Accessibility Assistant 05)
Il report di accessibilità (WCAG) finora era **effimero**: serviva solo a correggere i mockup e non
veniva salvato. Ora può essere **persistito** come deliverable del pacchetto, a scelta:
- L'Orchestrator, al momento dei mockup, chiede se salvare anche il report (opzione `persist_a11y`);
  di default resta effimero come prima.
- Se sì, il report viene committato in `requirements/a11y-report.md` (+ copia inglese) e registrato
  nel manifest con la nuova chiave `a11y`.
- Il Mockup Designer lo inoltra all'Orchestrator; l'Accessibility Assistant produce le due copie
  quando richiesto (continua a non scrivere file da solo).

### 5. (Follow-up) Schema del manifest aggiornato (contratto)
Lo schema `afu-manifest.schema.json` ora ammette la nuova chiave `a11y` (report + copia inglese) e —
correggendo un disallineamento del feedback round — le chiavi delle **copie inglesi del playbook**
(`playbook_en_md`, `playbook_en_xlsx`). Verificato che un manifest con queste chiavi passa la
validazione.

---

## Parte 3 — Come è stato portato su main (tracciabilità)

| Repository | Pull request | Contenuto | Commit di merge |
|---|---|---|---|
| Marketplace (corporate) | **PR #1** | Redesign AFU + feedback round (in un'unica PR, conflitti sui JSON generati risolti rigenerandoli dal sorgente) | `593c8eb` |
| Marketplace (corporate) | **PR #3** | Follow-up round | `f3aac73` |
| claude-flow (personale) | **PR #3** | Feedback round | `d1a5a08` |
| claude-flow (personale) | **PR #4** | Follow-up round | `1564770` |

**Controlli di qualità eseguiti:**
- Sul follow-up round è stata fatta una **review avversariale** che ha trovato 5 problemi (tra cui
  uno schema del manifest che avrebbe rifiutato la nuova chiave, e la mancata attivazione lato
  Orchestrator dell'opzione di salvataggio report): **tutti risolti e ri-verificati**.
- Le 9 skill, lo schema e l'executor sono **byte-identici** tra la sorgente (`claude-flow`) e la
  copia pubblicata nel plugin `sdlc-suite`.
- I 6 file JSON degli agenti sono rigenerati dal sorgente `.md` (unica fonte di verità).
