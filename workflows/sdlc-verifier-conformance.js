export const meta = {
  name: 'sdlc-verifier-conformance',
  description: 'Verifica deep di conformità AFU↔implementazione (miglioria #4): esplorazione statica read-only per requisito (matrice AFU↔codice + AC→test + Contratto UI), adversarial-verify per requisito (istanze scettiche che tentano di REFUTARE la copertura), completeness-critic ("nessun requisito AFU non verificato"). Ritorna findings + task T-VER proposti + over-implementation + verdetto. NON scrive nulla: l\'agente principale (single-writer) presenta il gate di approvazione e scrive TASKS/PROGRESS/VERIFICATION/CHANGELOG.',
  phases: [
    { title: 'Explore', detail: 'evidenza statica read-only per requisito (codice + AC→test + Contratto UI)' },
    { title: 'Verify', detail: 'adversarial-verify per requisito (panel scettico che prova a refutare la copertura)' },
    { title: 'Critic', detail: 'completeness-critic: nessun requisito AFU non verificato + over-implementation' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale — vedi skill sdlc-verifier):
//   scope:        {kind:'plan'|'feature'|'wave'|'tasks', label}
//   requirements: [{ref, kind:'req'|'AC'|'SC', feature, text, planned:boolean, status}]
//   repos:        [{nome, sigla, path, type}]
//   ui_contract_excerpt: string   (### Schermate & Interazioni per gli SC in scope, #1)
//   contracts_excerpt:   string   (CONTRACTS.md per gli endpoint in scope)
//   changelog_excerpt:   string   (## Piani + ultime attività, #3)
//   matrix_excerpt:      string   (Matrice di verifica dell'analyzer, se presente)
//   dynamic: {available:['playwright'|'chrome-devtools'|...], app_url, auth_hint}  (o vuoto → solo statico)
//   profile, const: oggetti | null
//   depth: 'standard'|'ultracode'   verifier_panel: number
// ---------------------------------------------------------------------------
const scope = (args && args.scope) || { kind: 'plan', label: '(intero piano)' }
const requirements = (args && Array.isArray(args.requirements)) ? args.requirements : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const uiContract = (args && args.ui_contract_excerpt) || ''
const contractsExcerpt = (args && args.contracts_excerpt) || ''
const changelogExcerpt = (args && args.changelog_excerpt) || ''
const matrixExcerpt = (args && args.matrix_excerpt) || ''
const dynamic = (args && args.dynamic) || {}
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3

const dynAvail = Array.isArray(dynamic.available) ? dynamic.available : []
const hasDynamic = dynAvail.length > 0 && !!dynamic.app_url

const EVIDENCE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ref: { type: 'string' },
    static_state: { type: 'string', enum: ['Coperto', 'Parziale', 'Mancante', 'Discrepanza'] },
    code_evidence: { type: 'string' },          // file:line o descrizione
    has_test: { type: 'boolean' },              // AC→test: esiste un test corrispondente?
    test_evidence: { type: 'string' },
    dynamic_applicable: { type: 'boolean' },
    dynamic_result: { type: 'string', enum: ['pass', 'fail', 'n/a'] },
    dynamic_evidence: { type: 'string' },       // screenshot/response/nota
    notes: { type: 'string' },
  },
  required: ['ref', 'static_state', 'code_evidence', 'has_test', 'dynamic_result'],
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ref: { type: 'string' },
    refuted: { type: 'boolean' },               // true = la copertura NON regge (skeptic ha refutato)
    reason: { type: 'string' },
    gap_kind: { type: 'string', enum: ['none', 'orphan', 'drift', 'ac-no-test', 'dynamic-fail'] },
  },
  required: ['ref', 'refuted', 'reason', 'gap_kind'],
}

const CRITIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    unverified_refs: { type: 'array', items: { type: 'string' } },     // requisiti AFU non verificati
    over_implementation: { type: 'array', items: { type: 'string' } }, // extra oltre l'AFU (report-only)
    notes: { type: 'string' },
  },
  required: ['unverified_refs', 'over_implementation'],
}

function reposBlock() {
  return repos.map(r => `  - ${r.sigla} (${r.type || '?'}): ${r.path}`).join('\n') || '  (nessun repo fornito)'
}
function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json: ${JSON.stringify(profile).slice(0, 4000)}\n`
  if (constJson) s += `CONST.json (principi inviolabili): ${JSON.stringify(constJson).slice(0, 3000)}\n`
  return s
}

function buildEvidencePrompt(req) {
  const dynLine = hasDynamic
    ? `Verifica DINAMICA disponibile (${dynAvail.join('/')}, app: ${dynamic.app_url}). Dove il requisito è osservabile sull'app reale, pilota il browser (FE: schermate/campi/valori/widget/trigger/trasversali dal Contratto UI) o chiama gli endpoint (BE: schema/errori vs CONTRACTS), registra pass/fail + evidenza (screenshot/response). Auth: ${dynamic.auth_hint || 'chiedi/statico se assente'}.`
    : `Nessun tool dinamico usabile → SOLO statico (dynamic_result="n/a", dynamic_applicable=false). COPERTURA RIDOTTA.`
  return `Sei sdlc-codebase-explorer in SOLA LETTURA. Raccogli l'EVIDENZA di conformità per UN requisito dell'AFU rispetto all'implementazione. NON modificare nulla.

Requisito [${req.ref}] (${req.kind}${req.feature ? `, ${req.feature}` : ''}): ${req.text}
Pianificato dall'analyzer: ${req.planned ? 'sì' : 'NO (potenziale orfano)'} — stato dichiarato: ${req.status || '?'}

Repo di codice (read-only):
${reposBlock()}

${ctxBlock()}${matrixExcerpt ? `Matrice di verifica (analyzer):\n${matrixExcerpt.slice(0, 4000)}\n` : ''}${uiContract ? `Contratto UI (#1) per gli SC in scope:\n${uiContract.slice(0, 4000)}\n` : ''}${contractsExcerpt ? `CONTRACTS.md (per la verifica BE):\n${contractsExcerpt.slice(0, 3000)}\n` : ''}
STATICO (sempre): mappa il requisito a evidenza nel codice → static_state ∈ {Coperto,Parziale,Mancante,Discrepanza} con code_evidence (file:line). Per gli AC: has_test = esiste un test corrispondente? (NON eseguire i test — verifica l'esistenza/corrispondenza). ${dynLine}`
}

function buildRefutePrompt(req, ev, k) {
  const lens = ['il requisito è davvero coperto dal codice citato?', 'esiste davvero un test per ogni AC?', 'il comportamento dinamico corrisponde all\'intento reale dell\'AFU?'][k % 3]
  return `Sei un verificatore scettico (istanza #${k + 1}, lente: "${lens}") della CONFORMITÀ AFU↔implementazione. SOLA LETTURA. Il tuo compito è tentare di REFUTARE la copertura dichiarata: default scettico.

Requisito [${req.ref}]: ${req.text}
Pianificato: ${req.planned ? 'sì' : 'NO'} — evidenza statica raccolta: ${ev ? JSON.stringify(ev).slice(0, 6000) : '(nessuna)'}

Refuta se: il requisito non è pianificato (orphan) → gap_kind="orphan"; è marcato done ma codice/comportamento non lo soddisfano (drift) → "drift"; un AC non ha test → "ac-no-test"; la verifica dinamica diverge dall'AFU → "dynamic-fail". Se la copertura REGGE davvero → refuted=false, gap_kind="none". In caso di dubbio (evidenza insufficiente) → refuted=true con reason esplicita. Verdetto per il singolo requisito.`
}

function buildCriticPrompt(findings) {
  return `Sei un completeness-critic della verifica di conformità AFU↔implementazione (scope: ${scope.label}). SOLA LETTURA.

Requisiti in scope (${requirements.length}): ${requirements.map(r => r.ref).join(', ')}
Findings prodotti: ${JSON.stringify(findings).slice(0, 12000)}

${changelogExcerpt ? `Changelog (cosa risulta done):\n${changelogExcerpt.slice(0, 3000)}\n` : ''}${uiContract ? `Contratto UI (per non dimenticare schermate/widget/trigger):\n${uiContract.slice(0, 3000)}\n` : ''}
Rispondi: (1) unverified_refs = requisiti AFU (incl. SC del Contratto UI e AC) in scope per cui MANCA una verifica/evidenza — il buco da colmare; (2) over_implementation = elementi presenti nell'implementazione che vanno OLTRE l'AFU (extra non richiesti) — SOLO report, nessun task. Sii esaustivo: meglio segnalare un dubbio che lasciarlo scoperto.`
}

// ---------------------------------------------------------------------------
if (!requirements.length) {
  log('Nessun requisito in args.requirements — niente da verificare.')
  return { meta_run: { scope: scope.label, requirements: 0, dynamic: hasDynamic }, findings: [], proposed_tasks: [], over_implementation: [], verdict: 'CONFORME' }
}

if (!hasDynamic) log('COPERTURA RIDOTTA (no dynamic): nessun tool dinamico usabile o app non fornita → verifica solo statica + AC→test.')

// Pipeline per requisito: evidenza statica/dinamica → adversarial-verify (panel scettico).
const findings = await pipeline(
  requirements,
  (req) => agent(buildEvidencePrompt(req), { label: `explore:${req.ref}`, phase: 'Explore', agentType: 'sdlc-codebase-explorer', schema: EVIDENCE_SCHEMA })
    .then(ev => ({ req, ev })),
  ({ req, ev }) => parallel(Array.from({ length: panel }, (_u, k) => () =>
      agent(buildRefutePrompt(req, ev, k), { label: `verify:${req.ref}#${k + 1}`, phase: 'Verify', schema: VERDICT_SCHEMA })))
    .then(votes => {
      const v = votes.filter(Boolean)
      const refuted = v.filter(x => x.refuted).length
      // Gate conservativo: nessun voto (panel fallito) → FLAG (non silenziare come conforme);
      // altrimenti gap se la maggioranza refuta.
      const isGap = v.length === 0 ? true : (refuted * 2 > v.length)
      const kinds = v.filter(x => x.refuted && x.gap_kind && x.gap_kind !== 'none').map(x => x.gap_kind)
      const gap_kind = isGap ? (kinds[0] || 'drift') : 'none'
      const reasons = v.length === 0
        ? ['nessun voto dal panel (verifier falliti) — verifica manuale richiesta']
        : (isGap ? v.filter(x => x.refuted).map(x => x.reason) : [])
      return {
        ref: req.ref, feature: req.feature || '', kind: req.kind, text: req.text,
        evidence: ev, gap: isGap, gap_kind,
        reasons,
        votes: v.length, refuted_count: refuted,
      }
    })
)

const clean = findings.filter(Boolean)

// Completeness-critic (barrier: serve la vista completa dei findings).
phase('Critic')
const critic = await agent(buildCriticPrompt(clean), { label: 'critic:completeness', phase: 'Critic', schema: CRITIC_SCHEMA }) || { unverified_refs: [], over_implementation: [] }

// Componi i task T-VER proposti (l'agente principale li presenta al gate di approvazione e li scrive).
const gapFindings = clean.filter(f => f.gap)
const proposed = gapFindings.map((f, i) => ({
  ref: `T-VER-${String(i + 1).padStart(2, '0')}`,
  afu_ref: f.ref, feature: f.feature, gap_kind: f.gap_kind,
  summary: `[${f.gap_kind}] ${f.text.slice(0, 120)}`,
  evidence: f.reasons.slice(0, 3),
}))
// requisiti non verificati segnalati dal critic ma non già in gapFindings → ulteriori task
const knownRefs = new Set(clean.map(f => f.ref))
;(critic.unverified_refs || []).filter(r => !knownRefs.has(r)).forEach((r, i) => {
  proposed.push({ ref: `T-VER-${String(proposed.length + 1).padStart(2, '0')}`, afu_ref: r, gap_kind: 'orphan', summary: `[unverified] ${r}`, evidence: ['non verificato (completeness-critic)'] })
})

const verdict = proposed.length ? 'NON-CONFORME'
  : ((critic.over_implementation || []).length || !hasDynamic) ? 'CONFORME-CON-RISERVE'
  : 'CONFORME'

log(`Conformità: ${clean.length} requisiti verificati, ${gapFindings.length} gap, ${proposed.length} task proposti → verdetto ${verdict}.`)

// NIENTE scrittura: l'agente principale presenta il gate di approvazione, poi scrive
// VERIFICATION.md + TASKS/PROGRESS + append [VERIFY] al changelog (single-writer).
return {
  meta_run: { scope: scope.label, requirements: requirements.length, dynamic: hasDynamic, tools: dynAvail, depth, panel },
  findings: clean,
  proposed_tasks: proposed,
  over_implementation: critic.over_implementation || [],
  verdict,
}
