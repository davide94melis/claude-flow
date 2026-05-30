export const meta = {
  name: 'sdlc-executor-wave',
  description: 'Esecuzione deep di UNA task di sdlc-executor: implementazione dei sotto-lavori indipendenti in parallelo (worktree isolati) per wave di dipendenza, verifica adversariale via sdlc-verifier, loop fix→riverifica (loop-until-dry). Ritorna proposte + verdetti + PATCH per sotto-lavoro; l\'applicazione dei patch (git apply), i commit e PROGRESS restano all\'agente principale, una task alla volta, con i gate utente (§8.1).',
  phases: [
    { title: 'Implement', detail: 'sotto-lavori per wave di dipendenza, worktree isolati' },
    { title: 'Verify', detail: 'sdlc-verifier (panel adversariale in ultracode) + loop fix→riverifica' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale dopo selezione task + branch, §3 skill):
//   task:     {id, descrizione, area, branch}
//   subjobs:  [{id, tipo, descrizione, depends_on:[id], repo_sigla, file_riferimento:[path]}]
//   repos:    [{nome, sigla, path}]
//   gap_excerpt: string  (estratto del gap report rilevante alla task)
//   profile, const: oggetti | null
//   depth: 'standard'|'ultracode'   verifier_panel: number   max_fix_iter: number (default 2)
// ---------------------------------------------------------------------------
const task = (args && args.task) || { id: '?', descrizione: '', area: '', branch: '' }
const subjobs = (args && Array.isArray(args.subjobs)) ? args.subjobs : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const gapExcerpt = (args && args.gap_excerpt) || ''
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3
const MAX_FIX = (args && Number(args.max_fix_iter)) ? Number(args.max_fix_iter) : 2

const IMPL_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    subjob_id: { type: 'string' },
    repo_sigla: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    diff_summary: { type: 'string' },     // sintesi leggibile delle modifiche
    patch: { type: 'string' },            // diff unificato applicabile (git diff) prodotto nel worktree
    tests_added: { type: 'array', items: { type: 'string' } },
    tests_passed: { type: 'boolean' },
    test_output: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['subjob_id', 'repo_sigla', 'files', 'diff_summary', 'patch', 'tests_passed', 'test_output', 'notes'],
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
    fase_a: { type: 'string' }, fase_b: { type: 'string' }, fase_c: { type: 'string' },
    problemi: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'problemi'],
}

function repoPath(sigla) {
  const r = repos.find(x => x.sigla === sigla)
  return r ? r.path : '(path repo non fornito)'
}
function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json (convenzioni/stack/dominio): ${JSON.stringify(profile)}\n`
  if (constJson) s += `CONST.json (principi inviolabili da rispettare): ${JSON.stringify(constJson)}\n`
  return s
}

function buildImplPrompt(sj, isFix, prevProblems) {
  const fixHdr = isFix
    ? `CORREZIONE: una verifica precedente ha dato FAIL. Risolvi SOLO questi problemi senza regressioni:\n${(prevProblems || []).map(p => `  - ${p}`).join('\n')}\n\n`
    : ''
  return `Implementa in SOLA-WORKTREE-ISOLATA il seguente sotto-lavoro della task ${task.id}. Sei un sottoagente implementatore: scrivi codice e test reali, poi lancia i test.

${fixHdr}Repo: ${sj.repo_sigla} — path: ${repoPath(sj.repo_sigla)}
Sotto-lavoro [${sj.id}] (${sj.tipo}): ${sj.descrizione}
File di riferimento (leggi per le convenzioni): ${(sj.file_riferimento || []).join(', ') || '(deduci dal codice)'}

${ctxBlock()}Estratto gap report rilevante:
${gapExcerpt.slice(0, 8000)}

Requisiti: implementa il sotto-lavoro completo (niente placeholder/TODO), scrivi test (happy path + edge + errori), poi ESEGUI i test e riporta l'output reale. In \`diff_summary\` un riassunto leggibile; in \`patch\` il diff unificato applicabile delle tue modifiche nel worktree corrente (\`git add -A && git diff --cached\`) — dev'essere sufficiente a una verifica indipendente. NON committare.`
}

function buildVerifyPrompt(sj, impl, k) {
  const lens = ['correttezza tecnica + test', 'coerenza col requisito (Fase B)', 'riesame: assunzioni nascoste/hardcoded/asserzioni (Fase C)'][k % 3]
  return `Sei sdlc-verifier (istanza scettica #${k + 1}, lente: ${lens}). Verifica in SOLA LETTURA il lavoro di un sottoagente sul sotto-lavoro [${sj.id}] della task ${task.id}. NON correggere.

Requisito: ${sj.descrizione}
Repo: ${sj.repo_sigla} (${repoPath(sj.repo_sigla)})
File modificati: ${(impl.files || []).join(', ')}
Patch (diff unificato delle modifiche):
${(impl.patch || impl.diff_summary || '').slice(0, 16000)}
Output test riportato: ${(impl.test_output || '').slice(0, 6000)}

Applica le 3 fasi (A tecnica/test, B coerenza requisito, C riesame) basandoti SUL PATCH e sull'output test forniti: l'implementazione vive in un worktree isolato NON accessibile da qui — NON rileggere il repo base (sarebbe lo stato pre-modifica). Default scettico: se manca una categoria di test, o un requisito non è implementato/testato, o ci sono hardcoded/assunzioni nascoste, o il payload è insufficiente a concludere → FAIL. Verdetto binario PASS/FAIL.`
}

// Verifica con panel: PASS solo se la maggioranza (>1/2) dà PASS; altrimenti FAIL.
async function verifySubjob(sj, impl) {
  const votes = (await parallel(Array.from({ length: panel }, (_u, k) => () =>
    agent(buildVerifyPrompt(sj, impl, k), { label: `verify:${sj.id}#${k + 1}`, phase: 'Verify', agentType: 'sdlc-verifier', schema: VERDICT_SCHEMA })
  ))).filter(Boolean)
  if (!votes.length) return { verdict: 'FAIL', problemi: ['nessun verdetto (verifier falliti)'], votes: 0 }
  const pass = votes.filter(v => v.verdict === 'PASS').length
  const verdict = pass * 2 > votes.length ? 'PASS' : 'FAIL'
  const problemi = verdict === 'FAIL' ? votes.flatMap(v => v.problemi || []) : []
  return { verdict, problemi, votes: votes.length, pass }
}

// Implementa + verifica un sotto-lavoro con loop-until-dry (bounded).
async function runSubjob(sj) {
  let impl = await agent(buildImplPrompt(sj, false), { label: `impl:${sj.id}`, phase: 'Implement', isolation: 'worktree', schema: IMPL_SCHEMA })
  if (!impl) return { subjob_id: sj.id, repo_sigla: sj.repo_sigla, status: 'IMPL_FAILED', verify: { verdict: 'FAIL', problemi: ['implementazione fallita'] }, iterations: 0, impl: null }
  let verify = await verifySubjob(sj, impl)
  let it = 0
  while (verify.verdict === 'FAIL' && it < MAX_FIX) {
    it++
    const fix = await agent(buildImplPrompt(sj, true, verify.problemi), { label: `fix:${sj.id}#${it}`, phase: 'Implement', isolation: 'worktree', schema: IMPL_SCHEMA })
    if (!fix) break
    impl = fix
    verify = await verifySubjob(sj, impl)
  }
  return {
    subjob_id: sj.id, repo_sigla: sj.repo_sigla, status: verify.verdict === 'PASS' ? 'VERIFIED' : 'NEEDS_ATTENTION',
    files: impl.files, diff_summary: impl.diff_summary, patch: impl.patch, tests_passed: impl.tests_passed, verify, iterations: it,
  }
}

// Wave per profondità di dipendenza (DAG topologico semplice su depends_on).
function buildWaves(jobs) {
  const byId = new Map(jobs.map(j => [j.id, j]))
  const depthByJob = new Map()
  const calc = (j, seen) => {
    if (depthByJob.has(j.id)) return depthByJob.get(j.id)
    if (seen.has(j.id)) return 0 // ciclo: tratta come radice
    seen.add(j.id)
    const deps = (j.depends_on || []).filter(d => byId.has(d))
    const d = deps.length ? 1 + Math.max(...deps.map(id => calc(byId.get(id), seen))) : 0
    depthByJob.set(j.id, d)
    return d
  }
  jobs.forEach(j => calc(j, new Set()))
  const maxD = jobs.length ? Math.max(...jobs.map(j => depthByJob.get(j.id))) : 0
  const waves = []
  for (let d = 0; d <= maxD; d++) waves.push(jobs.filter(j => depthByJob.get(j.id) === d))
  return waves
}

// ---------------------------------------------------------------------------
if (!subjobs.length) {
  log('Nessun sotto-lavoro in args.subjobs — niente da implementare.')
  return { meta_run: { task: task.id, subjobs: 0 }, results: [], all_verified: true, partial: false }
}

phase('Implement')
const waves = buildWaves(subjobs)
log(`Task ${task.id}: ${subjobs.length} sotto-lavori in ${waves.length} wave (depth=${depth}, panel=${panel}).`)
const results = []
for (let w = 0; w < waves.length; w++) {
  phase('Implement')
  log(`Wave ${w}: ${waves[w].length} sotto-lavori in parallelo (worktree isolati).`)
  const waveRes = await parallel(waves[w].map(sj => () => runSubjob(sj)))
  results.push(...waveRes.filter(Boolean))
}

const verified = results.filter(r => r.status === 'VERIFIED')
const failed = results.filter(r => r.status !== 'VERIFIED')
log(`Completato: ${verified.length}/${results.length} sotto-lavori verificati (PASS).`)

// Proposta: l'agente principale APPLICA i patch dei sotto-lavori VERIFIED uno alla volta (git apply), con i gate,
// e fa commit/PROGRESS (single-writer §8.1). Se failed.length>0 → §8.2: non applicare nulla,
// presenta lo stato e fai decidere l'utente.
return {
  meta_run: { task: task.id, branch: task.branch, subjobs: subjobs.length, waves: waves.length, depth, panel, verified: verified.length, failed: failed.length },
  results,
  all_verified: failed.length === 0,
  partial: failed.length > 0,
}
