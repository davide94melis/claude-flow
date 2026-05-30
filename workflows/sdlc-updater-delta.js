export const meta = {
  name: 'sdlc-updater-delta',
  description: 'Verifica deep del delta di sdlc-updater: gap-check read-only del delta (NUOVO/MODIFICATO) contro il codice per repo, completeness-critic sul delta, adversarial-verify sui MODIFICATO che ricadono su task già Completate (falso "invariato" = lavoro perso). Ritorna una PROPOSTA; PLAN/TASKS/PROGRESS li scrive l\'agente principale (single-writer).',
  phases: [
    { title: 'GapCheck', detail: 'explorer read-only per repo: classifica i delta nel codice' },
    { title: 'Verify', detail: 'completeness sul delta + adversarial sui MODIFICATO-su-task-completate' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale dopo la detection delta 2.2, stateful):
//   delta: [{ref, tipo:'NUOVO'|'MODIFICATO'|'RIMOSSO', funzionalita, cosa_cambia, riferimento}]
//   repos: [{nome, sigla, path}]
//   completed_tasks: [{id, descrizione, requisito}]   (task con stato Completata)
//   profile, const: oggetti|null   depth, verifier_panel
// ---------------------------------------------------------------------------
const delta = (args && Array.isArray(args.delta)) ? args.delta : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const completedTasks = (args && Array.isArray(args.completed_tasks)) ? args.completed_tasks : []
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3

const STATI = ['Coperto', 'Parziale', 'Mancante', 'Discrepanza', 'Da chiarire']
// Solo NUOVO/MODIFICATO vanno verificati nel codice (RIMOSSO si tratta a parte).
const toCheck = delta.filter(d => d.tipo === 'NUOVO' || d.tipo === 'MODIFICATO')
// Lookup autoritativo sui delta in input (source of truth del `tipo`, non l'output LLM).
const deltaByRef = Object.fromEntries(toCheck.map(d => [d.ref, d]))
const modRefs = new Set(toCheck.filter(d => d.tipo === 'MODIFICATO').map(d => d.ref))

const GAPCHECK_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    repo: { type: 'string' },
    items: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          ref: { type: 'string' }, stato: { type: 'string', enum: STATI },
          evidenze: { type: 'string' }, gap: { type: 'string' },
        },
        required: ['ref', 'stato', 'evidenze', 'gap'],
      },
    },
  },
  required: ['repo', 'items'],
}
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    delta_classified: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          ref: { type: 'string' }, tipo: { type: 'string', enum: ['NUOVO', 'MODIFICATO', 'RIMOSSO'] }, funzionalita: { type: 'string' },
          stato_codice: { type: 'string', enum: STATI }, evidenze: { type: 'string' },
          impatto_task: { type: 'string' }, task_completate_coinvolte: { type: 'array', items: { type: 'string' } },
        },
        required: ['ref', 'tipo', 'funzionalita', 'stato_codice', 'evidenze', 'impatto_task', 'task_completate_coinvolte'],
      },
    },
  },
  required: ['delta_classified'],
}
const COMPLETENESS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    missing: { type: 'array', items: { type: 'string' } },   // delta senza classificazione
    note: { type: 'string' },
  },
  required: ['missing', 'note'],
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    still_satisfied: { type: 'boolean' },   // la task completata soddisfa ANCORA il requisito modificato?
    evidence: { type: 'string' }, reasoning: { type: 'string' },
  },
  required: ['still_satisfied', 'evidence', 'reasoning'],
}

function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json: ${JSON.stringify(profile)}\n`
  if (constJson) s += `CONST.json: ${JSON.stringify(constJson)}\n`
  return s
}
function deltaBlock() {
  return toCheck.map(d => `- [${d.ref}] (${d.tipo}) ${d.funzionalita}: ${d.cosa_cambia} (rif: ${d.riferimento || '—'})`).join('\n')
}

function buildGapCheckPrompt(repo) {
  return `Sei sdlc-codebase-explorer, SOLA LETTURA. Per ciascun delta di requisito qui sotto, classifica lo stato NEL CODICE del repo ${repo.sigla} (${repo.path}). Non modificare nulla.

${ctxBlock()}Delta da verificare:
${deltaBlock()}

Per ogni delta pertinente a questo repo restituisci una riga {ref, stato (${STATI.join('/')}), evidenze (path), gap}. Ometti i delta non pertinenti a questo repo.`
}

function buildSynthPrompt(perRepo) {
  return `Fondi le classificazioni per-repo del delta in una classificazione per-delta cross-repo. Per ogni delta NUOVO/MODIFICATO indica stato_codice aggregato, evidenze, impatto sulle task, e quali task GIÀ COMPLETATE sono coinvolte.

Delta:
${deltaBlock()}

Task completate (attenzione ai MODIFICATO che le toccano):
${completedTasks.map(t => `- ${t.id}: ${t.descrizione} (req: ${t.requisito || '—'})`).join('\n') || '(nessuna)'}

Classificazioni per-repo (JSON):
${JSON.stringify(perRepo).slice(0, 100000)}

Restituisci delta_classified[]. Non inventare delta non presenti.`
}

function buildCompletenessPrompt(synth) {
  return `COMPLETENESS-CRITIC sul delta: ogni delta NUOVO/MODIFICATO ha una classificazione in delta_classified? Segnala i \`missing\` (ref senza riga).

Delta attesi: ${toCheck.map(d => d.ref).join(', ') || '(nessuno)'}
Classificati (JSON): ${JSON.stringify((synth && synth.delta_classified) || []).slice(0, 60000)}`
}

function buildAdvPrompt(item, k) {
  return `Sei sdlc-verifier (scettico #${k + 1}). Un requisito MODIFICATO ricade su una/più task GIÀ COMPLETATE. Verifica in SOLA LETTURA se il codice di quelle task soddisfa ANCORA il requisito *modificato* (un falso "invariato" = lavoro perso; un falso "modificato" = T-fix inutili).

Delta [${item.ref}] (${item.funzionalita}). Cosa cambia nel requisito: ${(deltaByRef[item.ref] && deltaByRef[item.ref].cosa_cambia) || '—'}
Posizioni codice da verificare: ${item.evidenze}
Task completate coinvolte: ${(item.task_completate_coinvolte || []).join(', ')}
Repo: ${repos.map(r => `${r.sigla}:${r.path}`).join(', ')}

Apri i file reali. still_satisfied=true se il codice esistente copre già il requisito modificato (nessun T-fix serve); false se serve un intervento. Default scettico: in dubbio false.`
}

// ---------------------------------------------------------------------------
if (!toCheck.length) {
  log('Nessun delta NUOVO/MODIFICATO da verificare nel codice.')
  return { meta_run: { delta: delta.length, to_check: 0 }, delta_classified: [], completeness: { missing: [], note: 'niente da verificare' }, adversarial: [] }
}
if (!repos.length) log('Nessun repo fornito: la classificazione nel codice sarà vuota.')

phase('GapCheck')
log(`GapCheck: ${toCheck.length} delta su ${repos.length} repo (depth=${depth}, panel=${panel}).`)
const perRepo = (await parallel(repos.map(r => () =>
  agent(buildGapCheckPrompt(r), { label: `gapcheck:${r.sigla}`, phase: 'GapCheck', agentType: 'sdlc-codebase-explorer', schema: GAPCHECK_SCHEMA })
))).filter(Boolean)

// §8.2: se NESSUN gapcheck è riuscito, non sintetizzare dal nulla (matrice allucinata).
if (repos.length && !perRepo.length) {
  log('Nessun gapcheck riuscito: salto sintesi/verifica, ritorno proposta vuota (§8.2).')
  return {
    meta_run: { delta: delta.length, to_check: toCheck.length, repos: repos.map(r => r.sigla), depth, panel, gapcheck_ok: 0 },
    delta_classified: [],
    completeness: { missing: toCheck.map(d => d.ref), note: 'gapcheck fallito: nessuna evidenza, sintesi saltata (§8.2)' },
    adversarial: [],
    rimossi: delta.filter(d => d.tipo === 'RIMOSSO').map(d => d.ref),
    partial: true,
  }
}

const synth = await agent(buildSynthPrompt(perRepo), { label: 'synthesize:delta', phase: 'GapCheck', schema: SYNTH_SCHEMA })
const classified = (synth && synth.delta_classified) || []

phase('Verify')
// MODIFICATO che toccano task completate → adversarial mirato.
const risky = classified.filter(d => modRefs.has(d.ref) && (d.task_completate_coinvolte || []).length)
log(`Verify: completeness sul delta + adversarial su ${risky.length} MODIFICATO-su-task-completate.`)
const [completeness, adversarial] = await Promise.all([
  agent(buildCompletenessPrompt(synth), { label: 'verify:completeness', phase: 'Verify', agentType: 'sdlc-verifier', schema: COMPLETENESS_SCHEMA }),
  parallel(risky.map(item => () =>
    parallel(Array.from({ length: panel }, (_u, k) => () =>
      agent(buildAdvPrompt(item, k), { label: `verify:mod:${item.ref}#${k + 1}`, phase: 'Verify', agentType: 'sdlc-verifier', schema: VERDICT_SCHEMA })
    )).then(votes => {
      const v = votes.filter(Boolean)
      const satisfied = v.filter(x => x.still_satisfied).length
      // conservativo: "ancora soddisfatto" solo con maggioranza; altrimenti serve T-fix
      const stillSatisfied = v.length ? (satisfied * 2 > v.length) : false
      return { ref: item.ref, task_completate_coinvolte: item.task_completate_coinvolte, still_satisfied: stillSatisfied, serve_tfix: !stillSatisfied, votes: v.length, evidenze: v.map(x => x.evidence) }
    })
  )),
])

return {
  meta_run: { delta: delta.length, to_check: toCheck.length, repos: repos.map(r => r.sigla), depth, panel, risky: risky.length },
  delta_classified: classified,
  completeness: completeness || { missing: [], note: 'completeness non disponibile' },
  adversarial,
  rimossi: delta.filter(d => d.tipo === 'RIMOSSO').map(d => d.ref),
}
