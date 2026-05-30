export const meta = {
  name: 'sdlc-reviewer-quality',
  description: 'Review deep della documentazione (sdlc-reviewer): analisi intra-documento in parallelo per doc + check read-only contro il codice per repo, sintesi inter-documento, poi completeness-critic + adversarial (bloccanti/ambiguità mancati) + judge-panel sulle assunzioni di Parte 2. Ritorna una PROPOSTA; CLARIFY.md/DOCX li scrive l\'agente principale (single-writer).',
  phases: [
    { title: 'Analyze', detail: 'per-documento (intra) + explorer per repo (check vs codice)' },
    { title: 'Synthesize', detail: 'inter-documento + merge problemi/assunzioni/disallineamenti' },
    { title: 'Verify', detail: 'completeness + adversarial (mancati) + judge-panel assunzioni' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale dopo conversione doc, Fase 2):
//   documents: [{nome, path}]   (MD convertiti in requirements/)
//   repos: [{nome, sigla, path}]   profile, const: oggetti|null
//   depth, verifier_panel
// ---------------------------------------------------------------------------
const documents = (args && Array.isArray(args.documents)) ? args.documents : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3

const CATEGORIE = ['Incoerenza', 'Gap funzionale', 'Ambiguità', 'Riferimento mancante', 'Disallineamento col codice']

const PROBLEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    categoria: { type: 'string', enum: CATEGORIE },
    bloccante: { type: 'boolean' },
    dove: { type: 'string' }, problema: { type: 'string' }, impatto: { type: 'string' },
    domanda: { type: 'string' }, assunzione_proposta: { type: 'string' },
  },
  required: ['categoria', 'bloccante', 'dove', 'problema', 'impatto', 'domanda', 'assunzione_proposta'],
}
const DOC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { documento: { type: 'string' }, problemi: { type: 'array', items: PROBLEMA } },
  required: ['documento', 'problemi'],
}
const CODE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    repo: { type: 'string' },
    disallineamenti: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { concetto_afu: { type: 'string' }, nel_codice: { type: 'string' }, file: { type: 'string' }, nota: { type: 'string' } },
        required: ['concetto_afu', 'nel_codice', 'file', 'nota'],
      },
    },
  },
  required: ['repo', 'disallineamenti'],
}
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    problemi: { type: 'array', items: PROBLEMA },
    assunzioni: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { ref: { type: 'string' }, problema_rif: { type: 'string' }, assunzione: { type: 'string' }, rischio: { type: 'string' }, costo: { type: 'string', enum: ['Basso', 'Medio', 'Alto'] } },
        required: ['ref', 'problema_rif', 'assunzione', 'rischio', 'costo'],
      },
    },
    disallineamenti: { type: 'array', items: CODE_SCHEMA.properties.disallineamenti.items },
  },
  required: ['problemi', 'assunzioni', 'disallineamenti'],
}
const COMPLETENESS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { issues: { type: 'array', items: { type: 'string' } }, note: { type: 'string' } },
  required: ['issues', 'note'],
}
const MISSED_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { missed: { type: 'array', items: PROBLEMA }, note: { type: 'string' } },
  required: ['missed', 'note'],
}
const JUDGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { davvero_non_bloccante: { type: 'boolean' }, rischio_corretto: { type: 'boolean' }, reasoning: { type: 'string' } },
  required: ['davvero_non_bloccante', 'rischio_corretto', 'reasoning'],
}

function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json (terminologia/dominio/stack): ${JSON.stringify(profile)}\n`
  if (constJson) s += `CONST.json: ${JSON.stringify(constJson)}\n`
  return s
}
const CAT_LIST = CATEGORIE.join(' / ')

function buildDocPrompt(doc) {
  return `Sei un revisore di documentazione funzionale (AFU), SOLA LETTURA. Analizza il documento e trova problemi di QUALITÀ documentale (non fare gap analysis tecnica).

Documento: ${doc.nome} — path: ${doc.path}
${ctxBlock()}
Verifica (3.1 intra-documento): coerenza interna, completezza dei flussi (caso felice + eccezioni/errori/alternativi), chiarezza dei requisiti (no requisiti vaghi), regole di business esplicitate (stati/transizioni/vincoli).
Per ogni problema: categoria (${CAT_LIST}), bloccante (true se senza risposta non si può pianificare in modo affidabile), dove (sezione), problema, impatto, domanda per il funzionale, e per i NON bloccanti una assunzione_proposta (cosa assumerà il team tech). Leggi il file reale.`
}

function buildCodePrompt(repo) {
  return `Sei sdlc-codebase-explorer, SOLA LETTURA. Check LEGGERO documentazione-vs-codice per il repo ${repo.sigla} (${repo.path}): trova punti dove l'AFU presuppone strutture/terminologie diverse da quelle nel codice (entità/campi, enum/stati, API/endpoint, transizioni). NON è gap analysis. Documenti AFU: ${documents.map(d => d.path).join(', ')}.
${ctxBlock()}
Restituisci i disallineamenti {concetto_afu, nel_codice, file, nota}.`
}

function buildSynthPrompt(docResults, codeResults) {
  return `Sintesi della review. Unisci i problemi per-documento (3.1), aggiungi i problemi inter-documento (3.2: AFU vs mockup, AFU vs specifiche, terminologia incoerente tra doc) e i disallineamenti col codice (3.3). Genera le assunzioni di Parte 2 (una per ogni problema NON bloccante, con ref A-NNN, rischio, costo Basso/Medio/Alto).

Documenti: ${documents.map(d => d.nome).join(', ')}
Problemi per-documento (JSON): ${JSON.stringify(docResults).slice(0, 90000)}
Disallineamenti codice (JSON): ${JSON.stringify(codeResults).slice(0, 40000)}

Restituisci problemi[] (dedup + inter-doc), assunzioni[] (A-NNN per i non bloccanti), disallineamenti[] (D-NNN). Non inventare.`
}

function buildCompletenessPrompt(synth) {
  return `COMPLETENESS-CRITIC della review. Verifica: ogni documento è stato analizzato? ogni problema BLOCCANTE ha una domanda? ogni problema NON bloccante ha una assunzione in Parte 2? ogni assunzione referenzia un problema esistente? Segnala gli \`issues\`.

Documenti attesi: ${documents.map(d => d.nome).join(', ')}
Sintesi (JSON): ${JSON.stringify(synth).slice(0, 80000)}`
}

function buildMissedPrompt(k) {
  const lens = ['regole di business non definite', 'eccezioni / flussi alternativi mancanti', 'terminologia ambigua / incoerente'][k % 3]
  return `Sei un revisore scettico #${k + 1} (lente: ${lens}). Rileggi i documenti AFU e cerca BLOCCANTI o AMBIGUITÀ che una prima passata può aver MANCATO, con questa lente. SOLA LETTURA.

Documenti: ${documents.map(d => `${d.nome} (${d.path})`).join(', ')}
${ctxBlock()}
Restituisci SOLO i problemi nuovi non ovvi (campo \`missed\`), con categoria/bloccante/dove/problema/impatto/domanda/assunzione_proposta. Se non trovi nulla di nuovo, \`missed\` vuoto.`
}

function buildJudgePrompt(a, k) {
  return `Sei un giudice scettico #${k + 1} su una assunzione di Parte 2. Valuta se è DAVVERO non-bloccante o se in realtà nasconde un bloccante, e se rischio/costo sono valutati correttamente. SOLA LETTURA dei documenti se serve.

Assunzione [${a.ref}] (rif ${a.problema_rif}): ${a.assunzione}
Rischio dichiarato: ${a.rischio} — costo: ${a.costo}
Documenti: ${documents.map(d => d.path).join(', ')}

davvero_non_bloccante=false se procedere con questa assunzione (senza chiarimento) può portare a una pianificazione sbagliata. Default scettico.`
}

// ---------------------------------------------------------------------------
if (!documents.length) {
  log('Nessun documento in args.documents — niente da analizzare.')
  return { meta_run: { documents: 0 }, problemi: [], assunzioni: [], disallineamenti: [], completeness: { issues: [], note: 'niente' }, missed: [], assunzioni_judged: [] }
}

phase('Analyze')
log(`Analyze: ${documents.length} doc (intra) + ${repos.length} repo (check codice), depth=${depth}, panel=${panel}.`)
const [docResults, codeResults] = await Promise.all([
  parallel(documents.map(d => () => agent(buildDocPrompt(d), { label: `doc:${d.nome}`, phase: 'Analyze', schema: DOC_SCHEMA }))),
  parallel(repos.map(r => () => agent(buildCodePrompt(r), { label: `code:${r.sigla}`, phase: 'Analyze', agentType: 'sdlc-codebase-explorer', schema: CODE_SCHEMA }))),
])

// §8.2: se NESSUNA analisi per-documento è riuscita, non sintetizzare dal nulla (review fantasma).
const docOk = docResults.filter(Boolean)
if (documents.length && !docOk.length) {
  log('Nessuna analisi per-documento riuscita: salto sintesi/verifica, ritorno proposta vuota (§8.2).')
  return {
    meta_run: { documents: documents.length, repos: repos.map(r => r.sigla), depth, panel, analyze_ok: 0 },
    problemi: [], assunzioni: [], disallineamenti: [],
    completeness: { issues: [], note: 'analyze fallito: nessuna evidenza, sintesi saltata (§8.2)' },
    missed: [], assunzioni_judged: [], partial: true,
  }
}

phase('Synthesize')
const synth = await agent(buildSynthPrompt(docOk, codeResults.filter(Boolean)), { label: 'synthesize:review', phase: 'Synthesize', schema: SYNTH_SCHEMA })
const assunzioni = (synth && synth.assunzioni) || []

phase('Verify')
log(`Verify: completeness + adversarial(mancati, ${panel} lenti) + judge-panel su ${assunzioni.length} assunzioni.`)
const [completeness, missedRounds, judged] = await Promise.all([
  agent(buildCompletenessPrompt(synth), { label: 'verify:completeness', phase: 'Verify', agentType: 'sdlc-verifier', schema: COMPLETENESS_SCHEMA }),
  parallel(Array.from({ length: panel }, (_u, k) => () => agent(buildMissedPrompt(k), { label: `verify:missed#${k + 1}`, phase: 'Verify', agentType: 'sdlc-verifier', schema: MISSED_SCHEMA }))),
  parallel(assunzioni.map(a => () =>
    parallel(Array.from({ length: panel }, (_u, k) => () => agent(buildJudgePrompt(a, k), { label: `judge:${a.ref}#${k + 1}`, phase: 'Verify', agentType: 'sdlc-verifier', schema: JUDGE_SCHEMA })))
      .then(votes => {
        const v = votes.filter(Boolean)
        const nonBlock = v.filter(x => x.davvero_non_bloccante).length
        const rischioOk = v.filter(x => x.rischio_corretto).length
        return { ref: a.ref, davvero_non_bloccante: v.length ? (nonBlock * 2 > v.length) : true, rischio_corretto: v.length ? (rischioOk * 2 > v.length) : true, votes: v.length, reasoning: v.map(x => x.reasoning) }
      })
  )),
])

const missed = (missedRounds || []).filter(Boolean).flatMap(r => r.missed || [])
log(`Verify completato: ${missed.length} problemi potenzialmente mancati; ${judged.filter(j => !j.davvero_non_bloccante).length} assunzioni contestate dal judge.`)

return {
  meta_run: { documents: documents.length, repos: repos.map(r => r.sigla), depth, panel },
  problemi: (synth && synth.problemi) || [],
  assunzioni,
  disallineamenti: (synth && synth.disallineamenti) || [],
  completeness: completeness || { issues: [], note: 'n/d' },
  missed,
  assunzioni_judged: judged,
}
