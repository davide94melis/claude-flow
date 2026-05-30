export const meta = {
  name: 'sdlc-analyzer-gap',
  description: 'Gap analysis deep di sdlc-analyzer: fan-out explorer per repo (×layer in ultracode), sintesi matrice gap, verifica completeness-critic + adversarial sui Coperto/Mancante. Ritorna una PROPOSTA strutturata; non scrive file (l\'agente principale finalizza e scrive PLAN/TASKS).',
  phases: [
    { title: 'Explore', detail: 'explorer read-only per repo (×layer in ultracode), barriera' },
    { title: 'Synthesize', detail: 'fusione output per-repo in bozza matrice gap' },
    { title: 'Verify', detail: 'completeness-critic + adversarial-verify su Coperto/Mancante' },
  ],
}

// ---------------------------------------------------------------------------
// Input (args, passati dall'agente principale dopo Fase 1-3.1 della skill):
//   repos:        [{nome, sigla, path}]
//   requirements: [{funzionalita, requisiti:[string]}]   (estratti in 3.1)
//   profile:      oggetto PROFILE.json | null  (null => explorer "senza profilo")
//   const:        oggetto CONST.json   | null
//   depth:        'standard' | 'ultracode'
//   max_concurrency: number   (informativo: il cap reale e' del Workflow tool)
//   verifier_panel:  number   (scettici per classificazione contestata)
// ---------------------------------------------------------------------------
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const requirements = (args && Array.isArray(args.requirements)) ? args.requirements : []
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3

const STATI = ['Coperto', 'Parziale', 'Mancante', 'Discrepanza', 'Da chiarire']

const LAYERS = [
  'modello dati / entità',
  'API / controller',
  'servizi / logica di business',
  'repository / query',
  'frontend / UI',
  'configurazione / sicurezza',
]

// Lenti adversariali (cicliche se verifier_panel supera la lunghezza)
const LENSES = [
  'correttezza funzionale',
  'completezza / edge case',
  'allineamento terminologico vs AFU',
  'sicurezza / side-effect',
  'coerenza dati / persistenza',
]

// ---------------------------------------------------------------------------
// Schemi (validati dal Workflow tool — i subagent ritornano oggetti conformi)
// ---------------------------------------------------------------------------
const EXPLORER_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    repo: { type: 'string' },
    layer: { type: 'string' },
    struttura: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { aspetto: { type: 'string' }, valore: { type: 'string' } },
        required: ['aspetto', 'valore'],
      },
    },
    gap_funzionalita: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          funzionalita: { type: 'string' },
          stato: { type: 'string', enum: STATI },
          file_coinvolti: { type: 'string' },
          gap: { type: 'string' },
        },
        required: ['funzionalita', 'stato', 'file_coinvolti', 'gap'],
      },
    },
    discrepanze: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          termine_doc: { type: 'string' },
          termine_codice: { type: 'string' },
          file: { type: 'string' },
          note: { type: 'string' },
        },
        required: ['termine_doc', 'termine_codice', 'file', 'note'],
      },
    },
  },
  required: ['repo', 'struttura', 'gap_funzionalita', 'discrepanze'],
}

const SYNTH_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    matrix_rows: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          requisito: { type: 'string' },
          funzionalita: { type: 'string' },
          repos_coinvolte: { type: 'array', items: { type: 'string' } },
          stato: { type: 'string', enum: STATI },
          evidenze: { type: 'string' },
          gap: { type: 'string' },
        },
        required: ['requisito', 'funzionalita', 'repos_coinvolte', 'stato', 'evidenze', 'gap'],
      },
    },
    gap_aperti: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { nome: { type: 'string' }, dettaglio: { type: 'string' } },
        required: ['nome', 'dettaglio'],
      },
    },
  },
  required: ['matrix_rows', 'gap_aperti'],
}

const COMPLETENESS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    orphan_requirements: { type: 'array', items: { type: 'string' } },
    extra_rows: { type: 'array', items: { type: 'string' } },
    note: { type: 'string' },
  },
  required: ['orphan_requirements', 'extra_rows', 'note'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    refuted: { type: 'boolean' },
    suggested_status: { type: 'string', enum: STATI },
    evidence: { type: 'string' },
    reasoning: { type: 'string' },
  },
  required: ['refuted', 'suggested_status', 'evidence', 'reasoning'],
}

// ---------------------------------------------------------------------------
// Helper di prompting
// ---------------------------------------------------------------------------
function profileBlock() {
  if (profile) return `PROFILE.json del progetto (convenzioni, tech stack, dominio, design system):\n${JSON.stringify(profile)}\n`
  return `NESSUN profilo fornito: opera in "modalità senza profilo" (deduci convenzioni e tech stack dai build file e dalla struttura, e documentale come se fossero un profilo).\n`
}
function constBlock() {
  return constJson ? `CONST.json (principi/standard inviolabili da considerare):\n${JSON.stringify(constJson)}\n` : ''
}
function requirementsBlock() {
  const lines = requirements.map(g => `- ${g.funzionalita}:\n` + (g.requisiti || []).map(r => `    • ${r}`).join('\n')).join('\n')
  return `Requisiti dall'AFU, raggruppati per funzionalità:\n${lines || '(nessun requisito fornito)'}\n`
}
function repoPathTable(sigle) {
  const list = (sigle && sigle.length) ? repos.filter(r => sigle.includes(r.sigla)) : []
  return (list.length ? list : repos).map(r => `  - ${r.sigla} (${r.nome}): ${r.path}`).join('\n')
}

function buildExplorerPrompt(unit) {
  const focus = unit.layer
    ? `Concentrati SOLO sul layer: "${unit.layer}". Ignora gli altri layer (saranno esplorati da agent paralleli).`
    : `Esplora tutti i layer rilevanti del repo.`
  return `Sei l'agente sdlc-codebase-explorer. Esplora in SOLA LETTURA il codebase e confrontalo con i requisiti AFU. Non modificare nulla.

Repo da esplorare: ${unit.repo.sigla} (${unit.repo.nome})
Path codebase: ${unit.repo.path}
${focus}

${profileBlock()}${constBlock()}${requirementsBlock()}

Per ogni funzionalità/requisito pertinente a questo repo${unit.layer ? '/layer' : ''}, classifica lo stato (${STATI.join(', ')}) con file/path esatti come evidenza, e annota le discrepanze terminologiche (termine AFU vs termine nel codice). Riporta SOLO ciò che riguarda questo repo${unit.layer ? ' e questo layer' : ''}. Restituisci l'oggetto strutturato richiesto (campo "repo"="${unit.repo.sigla}"${unit.layer ? `, "layer"="${unit.layer}"` : ''}).`
}

function buildSynthPrompt(explored) {
  return `Sei l'agente di SINTESI della gap analysis. Ricevi gli output read-only di più explorer (uno per repo${depth === 'ultracode' ? ' × layer' : ''}) e la lista requisiti AFU. Fondili in una BOZZA di matrice di verifica: UNA riga per requisito AFU (non per documento o modulo), con lo stato cross-repo.

Repo coinvolte (sigle):
${repoPathTable()}

${requirementsBlock()}

Output degli explorer (JSON):
${JSON.stringify(explored).slice(0, 120000)}

Regole di sintesi:
- Una riga per ogni requisito AFU; \`repos_coinvolte\` = sigle dei repo pertinenti.
- \`stato\` ∈ ${STATI.join(', ')} aggregando gli explorer (se un repo è Mancante e un altro Coperto per parti diverse dello stesso requisito, valuta Parziale).
- \`evidenze\`: path esatti file/classi per repo (sigla: path).
- \`gap\`: cosa manca o diverge, con dettaglio sufficiente a implementare senza rileggere l'AFU.
- \`gap_aperti\`: i gap principali in forma narrativa.
Non inventare requisiti non presenti nell'AFU. Non scrivere file: restituisci solo l'oggetto strutturato.`
}

function buildCompletenessPrompt(synth) {
  return `Sei il COMPLETENESS-CRITIC. Verifica che la bozza di matrice copra TUTTI i requisiti AFU, senza requisiti orfani (un requisito senza riga) né righe spurie (una riga senza requisito AFU corrispondente).

${requirementsBlock()}

Righe della matrice (JSON):
${JSON.stringify((synth && synth.matrix_rows) || []).slice(0, 100000)}

Restituisci: orphan_requirements (requisiti AFU senza riga), extra_rows (righe senza requisito AFU), note (sintesi). Sii rigoroso: ogni requisito estratto in 3.1 deve avere una riga.`
}

function buildSkepticPrompt(row, k) {
  const challenge = row.stato === 'Coperto'
    ? `La riga è classificata "Coperto". Prova a REFUTARLO: cerca nel codice prove che NON sia interamente coperto (parti mancanti, stub, comportamento divergente dall'AFU). Default scettico.`
    : `La riga è classificata "Mancante". Prova a REFUTARLO: cerca nel codice prove che in realtà ESISTA (magari con nome/posizione diversa che l'explorer ha mancato). Default scettico.`
  return `Sei uno scettico #${k + 1} di un panel adversariale di verifica della gap analysis (lente: ${LENSES[k % LENSES.length]}). Lavori in SOLA LETTURA sul codice reale.

Requisito: "${row.requisito}" (funzionalità: ${row.funzionalita})
Stato proposto: ${row.stato}
Evidenze dell'analisi: ${row.evidenze}
Repo coinvolte e path:
${repoPathTable(row.repos_coinvolte)}

${challenge}

Apri i file reali e controlla con i tuoi occhi. Se l'evidenza regge → refuted=false (lo stato proposto è corretto). Se trovi controprove → refuted=true e indica suggested_status (${STATI.join(', ')}) + evidence (path/snippet). In dubbio resta conservativo.`
}

// ---------------------------------------------------------------------------
// Riconciliazione adversariale (§8.3): maggioranza semplice (>1/2 dei voti) ribalta
// la classificazione; pareggio (panel pari) → "Da chiarire" (la più conservativa).
// Con il panel di default = 3 questo coincide con ≥2/3.
// ---------------------------------------------------------------------------
function mode(arr) {
  const c = {}
  let best = null, bestN = 0
  for (const x of arr) { c[x] = (c[x] || 0) + 1; if (c[x] > bestN) { bestN = c[x]; best = x } }
  return best
}

function reconcile(row, votes) {
  const total = votes.length
  if (!total) {
    return { requirement: row.requisito, repos: row.repos_coinvolte || [], status_originale: row.stato, status_riconciliato: row.stato, controprove: [], votes_refuted: 0, votes_total: 0, note: 'nessun verdetto (agent falliti)' }
  }
  const refuted = votes.filter(v => v.refuted)
  let status_riconciliato = row.stato
  let controprove = []
  if (refuted.length * 2 > total) {
    // Maggioranza ha refutato: NON può restare lo stato originale. Escludi eventuali
    // suggested_status == stato originale (verdetto contraddittorio) prima del mode.
    const suggestions = refuted.map(v => v.suggested_status).filter(s => s !== row.stato)
    status_riconciliato = mode(suggestions) || 'Da chiarire'
    controprove = refuted.map(v => v.evidence)
  } else if (refuted.length * 2 === total) {
    status_riconciliato = 'Da chiarire'
    controprove = refuted.map(v => v.evidence)
  }
  return {
    requirement: row.requisito,
    repos: row.repos_coinvolte || [],
    status_originale: row.stato,
    status_riconciliato,
    controprove,
    votes_refuted: refuted.length,
    votes_total: total,
  }
}

function short(s, n) { return (s || '').length > n ? (s.slice(0, n) + '…') : (s || '') }

// ---------------------------------------------------------------------------
// Orchestrazione
// ---------------------------------------------------------------------------
if (!repos.length) {
  log('Nessun repo in args.repos — niente da esplorare. Restituisco proposta vuota.')
}

// Unità di esplorazione: per repo (standard) o per repo×layer (ultracode)
const units = []
for (const r of repos) {
  if (depth === 'ultracode') {
    for (const layer of LAYERS) units.push({ repo: r, layer })
  } else {
    units.push({ repo: r, layer: null })
  }
}

phase('Explore')
log(`Explore: ${units.length} unità (${repos.length} repo, depth=${depth}, panel=${panel}).`)
const exploreResults = await parallel(units.map((u) => () =>
  agent(buildExplorerPrompt(u), {
    label: `explore:${u.repo.sigla}${u.layer ? ':' + short(u.layer, 10) : ''}`,
    phase: 'Explore',
    agentType: 'sdlc-codebase-explorer',
    schema: EXPLORER_SCHEMA,
  })
))
const explored = exploreResults.filter(Boolean)
log(`Explore completato: ${explored.length}/${units.length} unità riuscite (barriera).`)

// §8.2: se NESSUN explorer è riuscito, non sintetizzare dal nulla (rischio matrice
// allucinata). Ritorna una proposta vuota segnalata: l'agente principale decide.
if (units.length && !explored.length) {
  log('Nessun explorer riuscito: salto sintesi e verifica, ritorno proposta vuota (§8.2).')
  return {
    meta_run: { depth, panel, repos: repos.map(r => r.sigla), explore_units: units.length, explore_ok: 0 },
    struttura_per_repo: [],
    matrix_draft: [],
    gap_aperti_draft: [],
    discrepanze: [],
    completeness: {
      orphan_requirements: requirements.flatMap(g => (g.requisiti || []).map(r => `${g.funzionalita}: ${r}`)),
      extra_rows: [],
      note: 'explore fallito: nessuna evidenza, sintesi saltata (§8.2)',
    },
    adversarial: [],
    reclassified: [],
    partial: true,
  }
}

phase('Synthesize')
// Sintesi = ruolo di aggregazione su dati già raccolti (output explorer in prompt):
// ritorna SOLO la bozza strutturata, non scrive file (lo ribadisce il prompt). Nessun
// agentType dedicato — non è né explore né verify; l'agente principale resta single-writer.
const synth = await agent(buildSynthPrompt(explored), {
  label: 'synthesize:gap-matrix',
  phase: 'Synthesize',
  schema: SYNTH_SCHEMA,
})
const matrixRows = (synth && synth.matrix_rows) || []
log(`Synthesize: ${matrixRows.length} righe di matrice (bozza).`)

phase('Verify')
// completeness-critic (1 agent) — gira in parallelo all'adversarial
const challengeRows = matrixRows.filter(r => r.stato === 'Coperto' || r.stato === 'Mancante')
log(`Verify: completeness-critic + adversarial su ${challengeRows.length} classificazioni (Coperto/Mancante), panel=${panel}.`)

// completeness-critic e scettici = ruoli di sdlc-verifier (§9), read-only.
const [completeness, adversarial] = await Promise.all([
  agent(buildCompletenessPrompt(synth), { label: 'verify:completeness', phase: 'Verify', agentType: 'sdlc-verifier', schema: COMPLETENESS_SCHEMA }),
  parallel(challengeRows.map((row) => () =>
    parallel(Array.from({ length: panel }, (_unused, k) => () =>
      agent(buildSkepticPrompt(row, k), {
        label: `verify:adv:${short(row.requisito, 18)}#${k + 1}`,
        phase: 'Verify',
        agentType: 'sdlc-verifier',
        schema: VERDICT_SCHEMA,
      })
    )).then((votes) => reconcile(row, votes.filter(Boolean)))
  )),
])

const reclassified = (adversarial || []).filter(a => a.status_originale !== a.status_riconciliato)
log(`Verify completato: ${reclassified.length} classificazioni riclassificate dall'adversarial.`)

// ---------------------------------------------------------------------------
// Proposta strutturata (l'agente principale finalizza e SCRIVE PLAN/TASKS)
// ---------------------------------------------------------------------------
return {
  meta_run: { depth, panel, repos: repos.map(r => r.sigla), explore_units: units.length, explore_ok: explored.length },
  struttura_per_repo: explored.map(e => ({ repo: e.repo, layer: e.layer || null, struttura: e.struttura })),
  matrix_draft: matrixRows,
  gap_aperti_draft: (synth && synth.gap_aperti) || [],
  discrepanze: explored.flatMap(e => e.discrepanze || []),
  completeness: completeness || { orphan_requirements: [], extra_rows: [], note: 'completeness non disponibile' },
  adversarial: adversarial || [],
  reclassified,
}
