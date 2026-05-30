# Golden-test — pilota `sdlc-analyzer` `classic` vs `deep`

> Gate §11 di [`ORCHESTRATION_INTEGRATION_DESIGN.md`](./ORCHESTRATION_INTEGRATION_DESIGN.md):
> validare il pattern `deep` **sulla sola** `sdlc-analyzer` prima di propagarlo alle altre skill.
> Difesa contro il rischio **V5** (divergenza non rilevabile tra i due rami).

## Perché esiste

L'analisi gap è LLM-driven, quindi `classic` (sequenziale) e `deep` (Workflow tool multi-agent + adversarial) possono divergere. Il golden-test produce i due gap report sullo **stesso input fisso** e ne misura la divergenza con un comparatore deterministico. Si procede alla propagazione (step 4–6) **solo se ogni divergenza è spiegabile**.

> **Eseguire in una sessione NUOVA e pulita.** Il run `deep` lancia molti agent in parallelo (costo token significativo, tempi non brevi) ed è non-deterministico: due run possono differire, per questo il confronto è rubric-based, non byte-exact.

## Strumenti (già costruiti in questo repo)

- `workflows/sdlc-analyzer-gap.js` — workflow `deep` (explore fan-out → sintesi → completeness-critic + adversarial). Restituisce una **proposta**; l'agente principale finalizza e scrive.
- `skills/sdlc-analyzer/SKILL.md` — ramo `deep` cablato in §3.2 / §3.3 / Fase 4 (classic invariato).
- `scripts/golden-compare-gap.py` — comparatore deterministico delle due `## Matrice di verifica`.

**Pre-requisito di deploy:** `bash scripts/sync-installed.sh --apply` (copia le skill aggiornate + `workflows/sdlc-analyzer-gap.js` in `~/.claude/`). Senza questo, il Workflow tool non risolve `name: sdlc-analyzer-gap`.

## Progetto reale di test — BancaAgente (modalità legacy)

5 repo di codice (4 hanno `.br-local.json` legacy → profilo in `deloitte-profiles`; `ba-web` senza config, **da confermare** in sessione):

| Sigla | Repo | Path |
|---|---|---|
| EM  | ba-email-manager     | `C:\Users\davmelis\Documents\Github\ba-email-manager` |
| GW  | ba-gateway           | `C:\Users\davmelis\Documents\Github\ba-gateway` |
| WEB | ba-web               | `C:\Users\davmelis\Documents\Github\ba-web` |
| BE  | ba-back-end          | `C:\Users\davmelis\Documents\Github\ba-back-end` |
| DM  | ba-document-manager  | `C:\Users\davmelis\Documents\Github\ba-document-manager` |

- **Sigle**: proposte qui sopra — confermare/adattare in Fase 1 della skill.
- **Profilo**: leggere `.br-local.json` da un repo (es. `ba-back-end`) per ricavare `profiles_repo` + `profilo` (CONST + PROFILE legacy). Se assente, l'explorer gira in "modalità senza profilo".
- **Documentazione**: `C:\Users\davmelis\Downloads\Documentazione_aggiornata_04_05_2026` — contiene **più** BR/AFU (Monitoraggio V6, Set-Up BR v28, Booking, censimento post-closing, macchine a stati, tracciati report). 

> **Scegliere UNA sola AFU come input fisso** del golden-test, così i due rami sono confrontabili. Proposta: **Monitoraggio** (`BR - Agency Desk Monitoraggio V6.docx` + `202604_Deck Mockup_Monitoraggio_v10.pptx` + `202604_Macchina Stati Monitoring_v1.xlsx`). Usare la **stessa identica** lista documenti per entrambi i run.

## Procedura (sessione pulita)

Tutti gli output vanno in una cartella **scratch** dedicata, MAI nei `plans/todo/` reali:

```bash
mkdir -p .golden/$(date +%F)
```

1. **Run `classic`** — invoca `sdlc-analyzer` forzando `classic` (flag `.sdlc-local.json` `orchestration_mode: classic`, oppure nessuna keyword). Stessa AFU fissa + stessi 5 repo. A fine analisi, **copia la sezione `## Matrice di verifica` del PLAN** (o l'intero PLAN) in `.golden/<data>/classic.md`.

2. **Run `deep`** — invoca `sdlc-analyzer` in `deep` (flag `orchestration_mode: deep`, oppure keyword "a fondo"/"esaustivo"). Stessa identica AFU + repo. Salva la matrice in `.golden/<data>/deep.md`.

   > Per non scrivere nei plan reali: indirizza l'output verso la cartella scratch, oppure esegui l'analisi e poi **sposta/copia** il PLAN prodotto in `.golden/<data>/deep.md` ed elimina la cartella di lavoro dal `plans/todo/` se creata.

3. **Confronto deterministico**:

```bash
python scripts/golden-compare-gap.py .golden/<data>/classic.md .golden/<data>/deep.md --out .golden/<data>/divergenza.md
```

Il report mostra: copertura (requisiti solo-deep / solo-classic), accordo classificazioni, gap trovati solo da un ramo, esito euristico.

## Criteri di accettazione (gate §11)

- **Copertura**: `deep` copre **≥** `classic` (il fan-out + adversarial deve trovare di più, non di meno). Se deep copre meno → indagare prima di propagare.
- **Divergenze spiegabili**: ogni riga in disaccordo deve avere una spiegazione plausibile (es. `Mancante`→`Coperto` perché l'adversarial ha trovato l'implementazione che l'explorer single-pass aveva mancato; `Coperto`→`Parziale` perché uno scettico ha trovato un gap reale).
- **Niente divergenze inspiegabili o contraddittorie** (es. classificazioni che si invertono senza evidenza). Se presenti → correggere il pattern (`workflows/sdlc-analyzer-gap.js` o i prompt) **prima** di step 4–5.

Registrare l'esito (PASS/da-correggere) in fondo a `.golden/<data>/divergenza.md` e, se PASS, dare il via libero alla propagazione (`sdlc-executor`, `sdlc-debug`, `sdlc-updater`, `sdlc-reviewer`).

## Note

- Il workflow **non scrive** file: propone. L'agente principale finalizza e scrive PLAN/TASKS, e committa (invarianti §9). Il golden-test confronta i PLAN finali, non i raw del workflow.
- `.golden/` è in `.gitignore`: gli artefatti del golden-test non vanno committati.
