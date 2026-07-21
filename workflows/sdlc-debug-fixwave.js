export const meta = {
  name: 'sdlc-debug-fixwave',
  description: 'Fix-wave deep di sdlc-debug per un batch di bug: root-cause read-only in parallelo, fix in worktree isolati con routing per-stack, verifica adversariale via sdlc-work-verifier, loop fix→riverifica (loop-until-dry). Ritorna proposte + verdetti + PATCH per bug; l\'applicazione dei patch (git apply), i commit, BUG_REPORT e la validazione funzionale (Fase 3) restano all\'agente principale / umani (§8.2).',
  phases: [
    { title: 'RootCause', detail: 'explorer read-only per bug (ipotesi + file coinvolti)' },
    { title: 'Fix', detail: 'fix in worktree isolati, routing per-stack' },
    { title: 'Verify', detail: 'sdlc-work-verifier (panel adversariale) + loop fix→riverifica' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale dopo selezione bug, §Fase 2 skill):
//   bugs:  [{id, titolo, descrizione, severita, sezione, task_collegata, repo_sigla, stack}]
//   repos: [{nome, sigla, path}]   profile, const: oggetti|null
//   depth: 'standard'|'ultracode'  verifier_panel: number  max_fix_iter: number (default 2)
// ---------------------------------------------------------------------------
const bugs = (args && Array.isArray(args.bugs)) ? args.bugs : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3
const MAX_FIX = (args && Number(args.max_fix_iter)) ? Number(args.max_fix_iter) : 2

// Routing per-stack → subagent_type (rispecchia la tabella della skill sdlc-debug).
// Ordine significativo: la PRIMA key che matcha vince → i framework specifici PRIMA dei
// linguaggi generici (es. 'spring' prima di 'java'). Rispecchia la tabella di sdlc-debug.
const STACK_ROUTING = {
  'spring boot': 'spring-boot-engineer', 'spring': 'spring-boot-engineer',
  '.net': 'csharp-developer', 'dotnet': 'csharp-developer', 'c#': 'csharp-developer',
  'django': 'django-developer', 'fastapi': 'fastapi-developer',
  'express': 'node-specialist', 'nestjs': 'node-specialist', 'node': 'node-specialist',
  'laravel': 'laravel-specialist', 'symfony': 'symfony-specialist',
  'angular': 'angular-architect', 'next': 'nextjs-developer', 'react': 'react-specialist',
  'vue': 'vue-expert', 'flutter': 'flutter-expert', 'golang': 'golang-pro', 'rust': 'rust-engineer',
  // generici DOPO i framework specifici
  'java': 'java-architect', 'kotlin': 'kotlin-specialist', 'python': 'python-pro',
  'swift': 'swift-expert', 'php': 'php-pro', 'go': 'golang-pro',
}
// Match per "parola" per le key alfanumeriche (confine non-alfanumerico): evita falsi
// positivi tipo 'go' dentro 'mongodb' o 'java' dentro 'javascript'. Le key con caratteri
// speciali (.net, c#) usano substring.
function routeAgent(stack) {
  const s = (stack || '').toLowerCase()
  for (const key of Object.keys(STACK_ROUTING)) {
    const alnum = /^[a-z0-9]+$/.test(key)
    const hit = alnum
      ? new RegExp('(^|[^a-z0-9])' + key + '([^a-z0-9]|$)').test(s)
      : s.includes(key)
    if (hit) return STACK_ROUTING[key]
  }
  return 'general-purpose'
}

const ROOTCAUSE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    bug_id: { type: 'string' },
    file_coinvolti: { type: 'array', items: { type: 'string' } },
    ipotesi_root_cause: { type: 'string' },
    confidenza: { type: 'string', enum: ['alta', 'media', 'bassa'] },
  },
  required: ['bug_id', 'file_coinvolti', 'ipotesi_root_cause', 'confidenza'],
}
const FIX_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    bug_id: { type: 'string' }, repo_sigla: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    diff_summary: { type: 'string' },
    patch: { type: 'string' },            // diff unificato applicabile (git diff) prodotto nel worktree
    tests_added: { type: 'array', items: { type: 'string' } },
    tests_passed: { type: 'boolean' }, test_output: { type: 'string' }, notes: { type: 'string' },
  },
  required: ['bug_id', 'repo_sigla', 'files', 'diff_summary', 'patch', 'tests_passed', 'test_output', 'notes'],
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
    problemi: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'problemi'],
}

function repoPath(sigla) { const r = repos.find(x => x.sigla === sigla); return r ? r.path : '(path non fornito)' }
function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json: ${JSON.stringify(profile)}\n`
  if (constJson) s += `CONST.json (principi inviolabili): ${JSON.stringify(constJson)}\n`
  return s
}

function buildRootCausePrompt(b) {
  return `Sei un esploratore read-only. Localizza la root-cause del bug, NON correggere.

Bug [${b.id}] (${b.severita}): ${b.titolo}
Descrizione: ${b.descrizione}
Sezione: ${b.sezione || '?'} — task collegata: ${b.task_collegata || '?'}
Repo: ${b.repo_sigla} (${repoPath(b.repo_sigla)})
${ctxBlock()}
Trova i file/righe probabilmente coinvolti e formula un'ipotesi di root-cause con un livello di confidenza. Solo lettura.`
}

function buildFixPrompt(b, rc, isFix, prevProblems) {
  const fixHdr = isFix ? `CORREZIONE: una verifica ha dato FAIL. Risolvi SOLO:\n${(prevProblems || []).map(p => `  - ${p}`).join('\n')}\n\n` : ''
  const rcBlock = rc ? `Ipotesi root-cause: ${rc.ipotesi_root_cause}\nFile coinvolti: ${(rc.file_coinvolti || []).join(', ')}\n` : ''
  return `Implementa in SOLA-WORKTREE-ISOLATA il fix del bug. Scrivi codice e test reali, poi lancia i test. NON committare.

${fixHdr}Bug [${b.id}] (${b.severita}): ${b.titolo}
Descrizione: ${b.descrizione}
Repo: ${b.repo_sigla} — path: ${repoPath(b.repo_sigla)}
${rcBlock}${ctxBlock()}
Correggi la causa (non solo il sintomo), aggiungi un test di regressione che fallirebbe senza il fix, esegui i test e riporta l'output reale. In \`diff_summary\` un riassunto leggibile; in \`patch\` il diff unificato applicabile delle tue modifiche nel worktree corrente (\`git add -A && git diff --cached\`), sufficiente a una verifica indipendente.`
}

function buildVerifyPrompt(b, fix, k) {
  const lens = ['il fix risolve davvero la causa + test di regressione', 'nessuna regressione introdotta', 'assunzioni nascoste/hardcoded/asserzioni deboli'][k % 3]
  return `Sei sdlc-work-verifier (istanza scettica #${k + 1}, lente: ${lens}) sul fix del bug [${b.id}]. SOLA LETTURA, NON correggere.

Bug: ${b.titolo} — ${b.descrizione}
Repo: ${b.repo_sigla} (${repoPath(b.repo_sigla)})
File modificati: ${(fix.files || []).join(', ')}
Patch (diff unificato delle modifiche):
${(fix.patch || fix.diff_summary || '').slice(0, 16000)}
Output test: ${(fix.test_output || '').slice(0, 6000)}

3 fasi (A tecnica/test, B il bug è davvero risolto, C riesame) basate SUL PATCH e sull'output test: il fix vive in un worktree isolato NON accessibile da qui — NON rileggere il repo base (sarebbe lo stato pre-fix). Default scettico: senza test di regressione, o se la causa non è risolta, o hardcoded, o payload insufficiente → FAIL. Verdetto binario PASS/FAIL.`
}

async function verifyBug(b, fix) {
  const votes = (await parallel(Array.from({ length: panel }, (_u, k) => () =>
    agent(buildVerifyPrompt(b, fix, k), { label: `verify:${b.id}#${k + 1}`, phase: 'Verify', agentType: 'sdlc-work-verifier', schema: VERDICT_SCHEMA })
  ))).filter(Boolean)
  if (!votes.length) return { verdict: 'FAIL', problemi: ['nessun verdetto (verifier falliti)'] }
  const pass = votes.filter(v => v.verdict === 'PASS').length
  return { verdict: pass * 2 > votes.length ? 'PASS' : 'FAIL', problemi: pass * 2 > votes.length ? [] : votes.flatMap(v => v.problemi || []), votes: votes.length }
}

async function runBug(b, rc) {
  const at = routeAgent(b.stack)
  let fix = await agent(buildFixPrompt(b, rc, false), { label: `fix:${b.id}`, phase: 'Fix', isolation: 'worktree', agentType: at, schema: FIX_SCHEMA })
  if (!fix) return { bug_id: b.id, repo_sigla: b.repo_sigla, status: 'FIX_FAILED', root_cause: rc || null, verify: { verdict: 'FAIL', problemi: ['fix fallito'] }, iterations: 0, agentType: at }
  let verify = await verifyBug(b, fix)
  let it = 0
  while (verify.verdict === 'FAIL' && it < MAX_FIX) {
    it++
    const f = await agent(buildFixPrompt(b, rc, true, verify.problemi), { label: `fix:${b.id}#${it}`, phase: 'Fix', isolation: 'worktree', agentType: at, schema: FIX_SCHEMA })
    if (!f) break
    fix = f
    verify = await verifyBug(b, fix)
  }
  return {
    bug_id: b.id, repo_sigla: b.repo_sigla, agentType: at,
    status: verify.verdict === 'PASS' ? 'VERIFIED' : 'NEEDS_ATTENTION',
    root_cause: rc || null, files: fix.files, diff_summary: fix.diff_summary, patch: fix.patch, verify, iterations: it,
  }
}

// ---------------------------------------------------------------------------
if (!bugs.length) {
  log('Nessun bug in args.bugs — niente da fixare.')
  return { meta_run: { bugs: 0 }, results: [], all_verified: true, partial: false }
}

phase('RootCause')
log(`Fix-wave: ${bugs.length} bug (depth=${depth}, panel=${panel}).`)
const rootCauses = (await parallel(bugs.map(b => () =>
  agent(buildRootCausePrompt(b), { label: `rootcause:${b.id}`, phase: 'RootCause', agentType: 'sdlc-codebase-explorer', schema: ROOTCAUSE_SCHEMA })
)))
const rcById = new Map(rootCauses.filter(Boolean).map(rc => [rc.bug_id, rc]))

phase('Fix')
// Fix in parallelo: ogni bug nel proprio worktree isolato (aree disgiunte, §8.4).
const results = (await parallel(bugs.map(b => () => runBug(b, rcById.get(b.id))))).filter(Boolean)

const verified = results.filter(r => r.status === 'VERIFIED')
const failed = results.filter(r => r.status !== 'VERIFIED')
log(`Fix-wave completata: ${verified.length}/${results.length} bug verificati (PASS).`)

// Proposta: l'agente principale applica i patch dei bug VERIFIED uno alla volta (git apply), aggiorna
// BUG_REPORT (append, ID sequenziali, counter), suggerisce i commit (mai automatici).
// La validazione funzionale (Fase 3) resta UMANA. §8.2: se failed → non applicare nulla.
return {
  meta_run: { bugs: bugs.length, depth, panel, verified: verified.length, failed: failed.length },
  results,
  all_verified: failed.length === 0,
  partial: failed.length > 0,
}
