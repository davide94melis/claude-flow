# High-Fidelity Mockup Pipeline — generatore `brand.md` + rework agenti Solaria

**Data:** 2026-07-15
**Stato:** Design approvato (brainstorming), in attesa di plan di implementazione (SP1 per primo)
**Repo coinvolti:**
- `claude-flow` — **SP1**: nuova skill `sdlc-brandkit` (`skills/sdlc-brandkit/`), componente riutilizzabile fidelity-diff (`scripts/`), hook da `skills/sdlc-profile-setup/`, mirror verso il marketplace via `scripts/sync-installed.sh`.
- `claude-marketplace-engineering-ped` — **SP2**: rework degli agenti Solaria `solaria-agents/agents/00-afu-orchestrator.md`, `03-mockup-designer.md`, `05-accessibility-assistant.md` (+ rigenerazione `agents/json/*` via `scripts/generate-agent-json.py`).
- SPEC/project repo del progetto (per BA: `banca-agente`) — **SP3**: il `brand.md` reale + assets, prodotti eseguendo SP1. Repo codebase (`ba-web`) letto in sola lettura come sorgente del design system.

**Relazione con design precedenti:**
- Estende [2026-06-12-solaria-fase1-agents-design.md](./2026-06-12-solaria-fase1-agents-design.md) (agenti Fase 1c): questo design **potenzia** il Mockup Designer (03) e l'Accessibility Assistant (05) senza cambiarne il ruolo.
- Si appoggia a [2026-05-19-sdlc-profile-const-split-design.md](./2026-05-19-sdlc-profile-const-split-design.md) e [2026-05-11-br-agents-profiles-design.md](./2026-05-11-br-agents-profiles-design.md): riusa `PROFILE.json.design_system`, la struttura standalone (`constitution/`, `references/`, `branding/`), e la convenzione `.sdlc-local.json` (fallback `.br-local.json`) con modalità `classic`/`deep`.

---

## 1. Contesto e problema

Il Mockup Designer (agent 03) produce oggi mockup **"example-grade"**: il suo prompt li inquadra come *"illustrative baselines, clearly example-grade — not final design"* e la sua unica fonte di stile è un `brand.md` **volutamente sottile** (una palette + un font + una lista di componenti attesi, come nei dataset di esempio). Con questo input, i mockup sono coerenti col brand ma **non** replicano 1:1 una piattaforma esistente.

L'obiettivo dell'utente è ottenere mockup **quasi-pixel-perfect** rispetto alla piattaforma attuale (post frontend-modernization di Banca Agente), **integrabili** nel prodotto reale — pur mantenendo gli agenti **agnostici** rispetto alla piattaforma.

Tre vincoli architetturali emersi dall'analisi del codice degli agenti:

1. **Lo slot `brand.md` esiste già.** Il Mockup Designer risolve il branding con precedenza: *`branding/brand.md` dal repo GitHub del progetto (read-only) > file caricati dall'analista (dataset) > dataset di fallback*, e "deriva ogni colore/tipografia/spacing token dal branding risolto". Non serve un canale nuovo: serve **arricchire l'input** e **alzare il tetto di fedeltà** dell'agente.
2. **Il Mockup Designer è un sub-agent che NON parla con l'analista** — solo l'Orchestrator (00) lo fa, e la UI interattiva rende solo per l'agente con cui l'analista chatta. Quindi il "chiedere se esiste un `brand.md` + screenshot" **deve stare nell'Orchestrator**, agganciato a **GATE-1** (dove già si opta per i mockup), che poi passa il contratto al Mockup Designer.
3. **Il `dataset/` è di Solaria, read-only per il team tech.** L'Orchestrator è esplicito: *"the dataset holds ONLY the registry + uploaded extra files + fallback — NEVER the project content"* e *"LOAD CONTEXT FROM THE REPOS"*. Quindi il nostro output (`brand.md` + assets) va scritto **nel contesto** (repo GitHub tech-owned: SPEC repo + codebase), **mai** nel `dataset/` di Solaria.

La soluzione è un sistema a **3 sottoprogetti** che condividono un **contratto** (`brand.md`): un **generatore agnostico** (SP1) che produce il contratto, un **rework della pipeline** (SP2) che lo consuma in alta fedeltà, e l'**istanza BA** (SP3) come prima applicazione e banco di validazione.

```
┌─ SP1 · GENERATORE (claude-flow) ─────────────────────────── AGNOSTICO
│   skill sdlc-brandkit: ispeziona un frontend qualsiasi +
│   (opz.) cattura screenshot da POC → emette brand.md + tokens.css
│   + assets/{screenshots,snippets}    │ produce
│                                       ▼
├─ CONTRATTO · brand.md (schema agnostico, 8 sezioni) ─────── LINCHPIN
│                                       │ consumato da
│                                       ▼
├─ SP2 · PIPELINE (marketplace-engineering-ped) ───────────── AGNOSTICO
│   00 GATE-1 esteso (chiede brand.md+screenshot, risolve dal CONTESTO)
│   03 HIGH-FIDELITY MODE   05 palette locked        │ applicato a
│                                       ▼
└─ SP3 · ISTANZA BA (banca-agente/branding + ba-web sorgente) SPECIFICO BA
    brand.md reale di BA generato da SP1, validato con fidelity-diff
```

---

## 2. Decisioni di design

Frutto del brainstorming, fissate prima del plan:

| # | Decisione | Scelta |
|---|---|---|
| D1 | Canale di input per l'alta fedeltà | Riusare lo slot esistente `brand.md` del Mockup Designer, arricchendolo (no canale nuovo) |
| D2 | Dove nasce il `brand.md` | Nuova **skill Claude Code** `sdlc-brandkit` in `claude-flow`, **agnostica** |
| D3 | Rapporto con `sdlc-profile-setup` | Skill **standalone** + **hook opzionale** a fine profile-setup ("genero anche il brand.md deep?") |
| D4 | Riferimenti visivi per la fedeltà | `brand.md` include **screenshot golden** + **snippet HTML/CSS** (prodotti dalla skill) |
| D5 | Copertura del contratto | Token completi + componenti **core/più usati** + **pagine** della piattaforma |
| D6 | Cattura screenshot | **Ibrida** con ladder di fallback (Playwright `channel:chrome` → bundled → CDP → path manuali → skip). Verificata funzionante (§4.4) |
| D7 | Consegna del file | Sia **canonico nel contesto** sia **copia esportabile** portabile; **mai** nel dataset Solaria |
| D8 | Repo-contesto canonico (BA) | **SPEC/project repo** (`banca-agente`) sotto `branding/`; `ba-web` è la **sorgente** letta, non il target |
| D9 | Profondità rework agenti | **Rework profondo** della pipeline (00 GATE-1 + risoluzione dal contesto; 03 hi-fi mode; 05 palette locked) |
| D10 | Fidelity-diff harness | **Componente separato riutilizzabile** (`claude-flow/scripts/`): auto in `deep` dentro SP1 **e** invocabile on-demand in `classic` |
| D11 | Agnosticità | Skill + agenti 100% agnostici (detection + presenza-contratto); solo l'**output** è BA-specifico |
| D12 | Modalità orchestrazione della skill | Segue la convenzione ecosistema: `classic` default / `deep` opt-in, niente escalation silenziosa |
| D13 | Struttura di questo spec | Doc **ombrello** con **SP1 dettagliato**; SP2/SP3 architetturali, con plan propri a seguire |
| D14 | Nome skill | `sdlc-brandkit` |

---

## 3. Il contratto — `brand.md` (schema agnostico)

È il **linchpin**: SP1 lo produce, SP2 lo consuma, SP3 ne è un'istanza. Markdown-first (il Mockup Designer legge markdown), con code-fence copia-incolla. Accanto al `brand.md` la skill emette `tokens.css` (gli stessi token come file CSS a sé, così i mockup lo possono inline-are → determinismo) e la cartella `assets/`.

### 3.1 — Struttura del file

```
branding/
├── brand.md                    # il contratto (sezioni sotto)
├── tokens.css                  # :root{--*} standalone, generato dai token
├── brand.export.md             # copia self-contained (snippet inline + screenshot base64/zip)
└── assets/
    ├── screenshots/            # golden reference PNG + manifest.json (schermata→file)
    └── snippets/               # HTML+CSS per componente/pagina
```

### 3.2 — Sezioni di `brand.md`

| # | Sezione | Contenuto |
|---|---|---|
| 1 | **Meta** | progetto, stack rilevato, commit sorgente, `fidelity_target`, data, `generated_by`, sorgenti dei token (file/DOM) |
| 2 | **Design tokens** | blocco `:root{--*}` copia-incolla: palette con **ramp completi**, semantici, testo, surface, border, focus; **tipografia** (`@font-face`/web-font, root size, scala h1–h6, pesi, line-height, letter-spacing); **spacing / radius / shadow / z-index / transizioni**; **breakpoint** + **dimensioni layout** (navbar/header/footer/sidebar/gap/grid) |
| 3 | **Base/reset CSS** | equivalente del reset applicato (es. Preflight) + compensazioni app, copia-incolla, così i mockup partono dalla stessa baseline |
| 4 | **Componenti** | per ognuno (core + più usati): anatomia, varianti, **stati** (default/hover/focus/active/disabled/invalid), sizing + **snippet HTML+CSS fedele** in `assets/snippets/` |
| 5 | **Pagine/layout** | shell ricorrenti (lista back-office, detail con tab, wizard, dashboard, form) come snippet di layout |
| 6 | **Screenshot di riferimento** | indice di `assets/screenshots/` + manifest schermata→file: ground-truth visivo per l'ancoraggio |
| 7 | **Direttive di fedeltà** | Do/Don't operativi ("incolla i token verbatim; non inventare colori; aggancia spacing alla scala; usa gli snippet come base") |
| 8 | **Locale + a11y** | lingua UI (IT), target WCAG (AA), nota **"palette locked"** per il pass accessibilità (§5.3) |

### 3.3 — Modello dei token (agnostico)

Nomi di token **stabili e neutri** (indipendenti dalla UI library sorgente), così SP2 li consuma sempre allo stesso modo:

```
--color-primary-{50..950}          --color-{success,warning,danger,info}-{...}
--color-surface-{0,50..950}        --color-text, --color-text-muted
--color-border                     --focus-ring-{color,width,offset}
--font-family-base                 --font-size-root, --font-size-{h1..h6,sm,xs}
--font-weight-{regular,medium,semibold,bold}   --line-height-base
--space-{0..N} (scala)             --radius-{sm,md,lg}   --shadow-{sm,md,lg}
--z-{dropdown,sticky,modal,toast}  --bp-{sm,md,lg,xl}
--layout-{navbar,header,footer}-h  --layout-sidebar-{open,closed}-w  --gap-{xs,md,lg}
```

La skill mappa i token della sorgente (CSS vars, theme preset, config utility-CSS) su questo modello; l'appendice A mostra l'istanza reale di BA.

---

## 4. SP1 — skill `sdlc-brandkit` (dettaglio)

### 4.1 — Collocazione, invocazione, modalità

- Path: `claude-flow/skills/sdlc-brandkit/SKILL.md` (+ `_snippet-template.md`, `_brand-template.md`). Mirror in `marketplace/plugins/sdlc-suite/skills/` via `sync-installed.sh`.
- Trigger (IT): *"genera il brand kit"*, *"genera il design spec"*, *"brand.md per i mockup"*, *"specifiche di stile per i mockup"*, *"design contract"*.
- Registrazione in `~/.claude/CLAUDE.md` come le altre skill (voce + trigger).
- **Modalità** `classic`/`deep` risolte dalla cascata standard (`.sdlc-local.json` → keyword → AskUserQuestion), banner sempre a video, niente escalation silenziosa. In `deep`: fan-out estrazione componenti per-area + **completeness-critic** + **fidelity-diff** (§6). Fallback rumoroso a `classic` con banner **COPERTURA RIDOTTA** se il Workflow tool non è disponibile.

### 4.2 — Input

- Path del/i repo frontend (riusa la detection di `sdlc-profile-setup` Step 3/4.2/4.4).
- (opz.) URL/POC in esecuzione per gli screenshot e per i computed-style dal DOM reale.
- (opz.) `PROFILE.json` esistente → riusa e approfondisce `design_system` invece di ripartire da zero.
- Repo-contesto target dove scrivere l'output (default: SPEC/project repo del profilo; §4.6).

### 4.3 — Pipeline (step)

1. **Detect** stack + sorgenti del design system: build files, variabili CSS/SCSS, **theme preset** (es. preset di design-system), **component styles**, config utility-CSS. Tabella di detection agnostica che estende `profile-setup` 4.2/4.4.
2. **Estrai token** → normalizza sul modello §3.3 (colori con ramp, tipografia, spacing, radius, border, shadow, z, breakpoint, layout). Genera `:root{--*}` + `tokens.css`.
3. **Estrai componenti** (core + più usati) → varianti/stati + **snippet HTML+CSS**. Sorgenti: component styles **+ (opz.) computed-style dal DOM reale** via browser headless sull'app in esecuzione (massima fedeltà su padding/line-height/ombre effettivi).
4. **Estrai pagine/layout** → identifica le shell ricorrenti e ne produce snippet di layout.
5. **Screenshot** (ladder ibrida §4.4) → cattura le golden reference dal POC/dev-server, costruisce `assets/screenshots/manifest.json`.
6. **Assembla** `brand.md` (8 sezioni) + `tokens.css` + `assets/` + `brand.export.md`.
7. **(deep) Verifica** → `completeness-critic` (coverage token/componenti/pagine dichiarata vs reale) + **fidelity-diff** (§6): render headless dello snippet ↔ regione dello screenshot golden → **fidelity score** per componente/pagina, con report dei delta.
8. **Presenta e conferma** → mostra riepilogo + score; scrive nel contesto **solo dopo conferma** (mai auto-commit sul codice).

### 4.4 — Cattura screenshot: ladder ibrida (verificata)

Verifica eseguita il 2026-07-15 su questa macchina (Netskope/policy corporate attive): **Playwright funziona** — Chromium bundled v149, Chrome di sistema via `channel:'chrome'` v150, e `page.goto` su server localhost, tutti OK con PNG reali.

```
1) Chrome di sistema  (Playwright channel:'chrome' — nessun download dalla CDN)   ← default
2) Chromium bundled   (se già in cache ms-playwright)
3) CDP connect        (chromium.connectOverCDP verso un Chrome avviato a mano con
                       --remote-debugging-port = la via "Chrome DevTools")
4) Path manuali       (l'utente fornisce screenshot già esistenti → indicizzati)
5) Skip               (solo token + snippet; banner "screenshot assenti")
```

Note operative: la CDN dei browser (blocco corporate #1) è aggirata da `channel:'chrome'`; la navigazione su `localhost`/POC non passa dal proxy; login/pagine autenticate → sessione via storage state o cattura manuale; **mai** salvare PII/segreti nelle immagini (rispetta `CONST.never_log`).

### 4.5 — Hook da `sdlc-profile-setup`

A fine `profile-setup` (dopo la scrittura di CONST/PROFILE), prompt opzionale: *"Genero anche il `brand.md` deep per i mockup ad alta fedeltà (sdlc-brandkit)?"* → se sì, invoca `sdlc-brandkit` col contesto già raccolto. La skill resta pienamente invocabile da sola.

### 4.6 — Output (nel contesto, mai nel dataset)

- **Canonico**: `<context-repo>/branding/{brand.md,tokens.css,assets/}`. Per BA: **SPEC/project repo `banca-agente`** (D8). Evitare il nome `dataset/branding/` (collide con l'area Solaria): usare `branding/` (o `references/branding/`) tech-owned.
- **Copia esportabile**: `brand.export.md` self-contained, anch'essa nel contesto. Se GitHub è giù, è **l'analista** a fare drag&drop in chat e **Solaria** a ingerirla come "uploaded extra": noi non scriviamo mai nel dataset.
- **Commit**: gated (nessun commit/push finché l'utente non lo chiede), pathspec esplicito.

### 4.7 — Agnosticità (SP1)

Tutto è detection-driven: nessun riferimento hardcoded a BA/PrimeNG/Aura nel corpo della skill. La tabella di detection cita gli stack come esempi, ma il flusso funziona per Angular/React/Vue/Svelte + qualsiasi UI library o CSS custom. BA è la **prima istanza** (§ appendice A), non un caso speciale nel codice.

---

## 5. SP2 — rework pipeline agenti (architetturale)

> Dettaglio + plan in uno spec dedicato. Qui l'architettura e i punti di innesto.

### 5.1 — `00-afu-orchestrator` (GATE-1 esteso + risoluzione dal contesto)

- A **GATE-1** (opt-in mockup), oltre a "genero i mockup?", **rileva/chiede** il contratto: cerca `branding/brand.md` **nel contesto** (SPEC repo + codebase repos via GitHub tool) e chiede se allegare screenshot; se presente, propone la **modalità alta fedeltà**.
- Passa al Mockup Designer `{fidelity:'high'|'baseline', brand_md, tokens_css, screenshots[], snippets[]}` in aggiunta al contesto già passato.
- **Risoluzione branding dal contesto**: aggiornare il wording perché il branding provenga dal contesto (repo), coerente con "il dataset non contiene mai project content"; il dataset resta solo fallback in lettura.
- Nessun brand.md/screenshot → comportamento attuale invariato (`fidelity:'baseline'`).

### 5.2 — `03-mockup-designer` (HIGH-FIDELITY MODE)

- Nuova modalità attivata dalla presenza di un contratto completo: **incolla i token verbatim** (inline `tokens.css`), **replica la grammar** dei componenti dagli snippet, **ancora agli screenshot** golden, **zero invenzione** di colori/spacing.
- Rilassa il framing "example-grade only" **solo** in hi-fi mode; in assenza di contratto resta l'attuale baseline example-grade.
- Invariati: architettura modulare/interattiva, export PNG/SVG, single-writer, boundary mockup-only, lingua IT.

### 5.3 — `05-accessibility-assistant` (palette locked)

- Rispetta la **palette locked** del brand: le remediation di contrasto devono restare **dentro i ramp** del brand o essere segnalate come **decisione brand-level**, **mai** override silenzioso dei colori del brand.
- Per il resto invariato: read-only, preserva architettura, report in IT.

### 5.4 — Rigenerazione JSON

Dopo l'edit dei `.md`, rigenerare `agents/json/*` con `scripts/generate-agent-json.py`. Verificare che il diff JSON rifletta solo le modifiche attese.

### 5.5 — Agnosticità (SP2)

La hi-fi mode si attiva sulla **presenza del contratto**, non su specifiche BA. Gli agenti non contengono nulla di BA-specifico.

---

## 6. Fidelity-diff — componente riutilizzabile (D10)

- Path: `claude-flow/scripts/fidelity-diff.<py|js>` (+ eventuale wrapper). Dipendenza immagine leggera (es. `pixelmatch`/equivalente) o confronto strutturale se non installabile.
- **Input**: uno snippet HTML (o un mockup) + uno screenshot golden (+ regione/selettore) → render headless (stessa ladder §4.4) → confronto → **score** + immagine di diff + soglia configurabile.
- **Uso**: (a) **auto** dentro SP1 in `deep` (step 7); (b) **on-demand in `classic`** come CLI/echo di supporto; (c) riutilizzabile in futuro da SP2 per una self-check del mockup.
- Degrada con eleganza: se il render non è possibile (policy), emette score "N/A" con banner, senza rompere il flusso.

---

## 7. SP3 — istanza BA (architetturale)

- Prodotta **eseguendo SP1 su `ba-web`** (+ dev-server locale per gli screenshot; build/serve con Node 20).
- **Output canonico**: `banca-agente/branding/{brand.md,tokens.css,assets/}` (D8), + `brand.export.md`.
- **Validazione**: giro completo brand.md+screenshot → 03 hi-fi su una schermata campione, con **fidelity-diff** vs BA reale; iterazione fino a soglia.
- I token reali di BA (appendice A) fungono anche da **test del contratto**: se lo schema §3 li rappresenta senza perdite, il contratto è adeguato.

---

## 8. Repo, commit policy, out of scope

**Repo toccati:** `claude-flow` (skill + script + hook), `claude-marketplace-engineering-ped` (3 agenti + json), `banca-agente` (brand.md + assets). `ba-web` letto in sola lettura.

**Commit policy:** nessun commit/push finché l'utente non lo chiede; sui repo condivisi commit con **pathspec esplicito** (mai `git add -A`); niente auto-commit sul codice; scritture su file source-of-truth single-writer.

**Fuori scope (YAGNI ora):** design finale di produzione; mockup esaustivi dei non-happy-path; multi-tema/multi-brand (BA è mono-tema); integrazione CI del fidelity-diff; refactor di agenti diversi da 00/03/05.

---

## 9. Ordine di esecuzione (prossimi passi)

```
Design doc (questo) → review utente
   ↓
SP1 · plan + implementazione skill sdlc-brandkit + fidelity-diff → esegui su ba-web → SP3 (brand.md BA)
   ↓
Validazione fidelity-diff sull'istanza BA (raffina il contratto §3 se emergono perdite)
   ↓
SP2 · plan + rework agenti 00/03/05 + regen json → prova end-to-end (brand.md BA → mockup hi-fi)
   ↓
Aggiornamento memory + eventuale commit/push (su richiesta utente, pathspec esplicito)
```

SP1 per primo perché SP2 e SP3 dipendono dal **contratto** che SP1 definisce e riempie. Ogni sottoprogetto avrà il proprio plan di implementazione (skill `writing-plans`).

---

## Appendice A — Istanza BA (estratta da `ba-web`, per validare il contratto)

Stack: Angular 21.2, PrimeNG 21.1.9, `@primeuix/themes` 2.0.3 (preset Aura custom `AgencyDeskPreset`), Tailwind v4 + `tailwindcss-primeui`, PrimeIcons 6, font **Space Grotesk** self-hosted (300–700). Root **14px**, `line-height` html **1.15**. Reset = Tailwind Preflight + compensazioni in `@layer base`.

| Token (modello §3.3) | Valore BA | Sorgente |
|---|---|---|
| `--color-primary-500` | `#2c8287` (teal) | `agency-desk-preset.ts` |
| primary hover / active | `#3d6f73` / `#294a4d` | preset (colorScheme.light) |
| ramp surface | slate (`slate.0..950`) | preset |
| `--color-text` / muted | `#212121` / `#666666` | preset (pinned) |
| `--color-border` | `#e2e8f0` (slate.200, bordo unico app) | preset / `_legacy-vars.scss` |
| focus ring | `#3f63f6`, 2px, offset 2px | preset |
| `--radius-md` | `6px` (uniforme) | preset (Aura md) / `--border-radius` |
| danger / invalid | `#cf4646` | `_legacy-vars.scss` (`--invalid-color`) |
| warning | `#cc8925` (`--warning-color`) | `_legacy-vars.scss` |
| brand accent | `#004a74` (`--brand-color`) | `_legacy-vars.scss` |
| success/ramp palette | Tailwind v4 palette bridged (`--color-green/red/yellow/...`) | `_legacy-vars.scss` |
| tipografia h1..h6 | 2em(bold) / 2 / 1.75 / 1.5 / 1.25 / 1.14286 rem | `_typography.scss` |
| tag label | `0.875rem` | `_typography.scss` (`.p-tag-label`) |
| layout | navbar 77 / header 60 / footer 66 px; sidebar 250/60 px; gap 60/42/24 px | `_variables.scss` |
| breakpoint | 768 / 992 (+ Tailwind default) | scss/media |

Componenti con delta noti rispetto ad Aura (da modellare in §3.4): button (filled teal; outlined/text trasparenti), input/select (14px, `line-height:normal`, bordo rosso invalid su dirty/touched), textarea (`.p-textarea`), tab "a bottone" (variante `practice-detail-tabs`), accordion header (`border-box`), initials-circle (avatar), number-circled, tag/badge. Pagine ricorrenti: lista back-office, detail pratica con tab, wizard/InfoPratica, dashboard.
