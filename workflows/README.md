# workflows/ — script di orchestrazione `deep` per le skill SDLC heavy

> Vedi [`docs/ORCHESTRATION_INTEGRATION_DESIGN.md`](../docs/ORCHESTRATION_INTEGRATION_DESIGN.md)
> (§3 Opzione C, §6 i due cerchi, §7 blueprint per skill, §10 struttura file).

Questa cartella contiene **uno script JS per skill SDLC *heavy***, eseguito dal
**Workflow tool** quando la skill gira in modalità `deep` (`orchestration_mode: "deep"`
in `.sdlc-local.json`). In modalità `classic` (default) questi script **non** vengono
usati: la skill esegue il ramo sequenziale storico.

Una `SKILL.md` è Markdown iniettato nel main-loop di Claude e **non** può chiamare
direttamente `parallel()` / `pipeline()` / `agent({schema})` — quelle sono primitive
del Workflow tool. Il pattern (Opzione C del design) è: in `deep` la skill **istruisce
Claude a invocare il Workflow tool** con lo script qui sotto, che fa il vero fan-out
parallelo, `adversarial-verify`, `completeness-critic` e `isolation:'worktree'`.
Gli **schema JSON** dei sub-agent vivono in questi script, **non** nel frontmatter
degli agent in `agents/` (lì il tool `Task` li ignorerebbe).

## Script previsti (rollout §11)

| Script | Skill | Stato |
|---|---|---|
| `sdlc-analyzer-gap.js` | `sdlc-analyzer` | da costruire (pilota, §11 step 3) |
| `sdlc-executor-wave.js` | `sdlc-executor` | da costruire (§11 step 4) |
| `sdlc-debug-fixwave.js` | `sdlc-debug` | da costruire (§11 step 4) |
| `sdlc-updater-delta.js` | `sdlc-updater` | da costruire (§11 step 5) |
| `sdlc-reviewer-quality.js` | `sdlc-reviewer` | da costruire (§11 step 5) |

Le skill *light* (`sdlc-estimator`, `sdlc-clarify`, `sdlc-progress-report`,
`sdlc-profile-setup`) **non** hanno uno script qui: in `deep` aggiungono solo un
singolo sub-step di `completeness/coherence-critic` (§6).

## Deploy

`scripts/sync-installed.sh --apply` copia `workflows/*.js` in `~/.claude/workflows/`,
da cui il Workflow tool li risolve per nome.

## Invarianti (validi anche in `deep`, §9)

Gate utente, niente auto-commit sul codice, single-writer serializzato sui file
source-of-truth, agent di verifica/esplorazione read-only, barriere dove la fase a
valle richiede lo stato completo. La degradazione a `classic` (Workflow tool assente
o fallimento) è **rumorosa**: banner "COPERTURA RIDOTTA" nell'artefatto.
