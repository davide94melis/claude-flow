export const meta = {
  name: 'sdlc-merge-integrate',
  description: 'Integrazione cross-piano deep (miglioria #2): overlap analysis parallela read-only per Piano/repo (file/entità/enum/contratti toccati), proposta d\'ordine impact/conflict-aware, adversarial-verify delle risoluzioni di conflitto, completeness-critic ("tutti i Piani integrati, nessun commit perso"). Ritorna overlaps + ordine proposto + conflitti semantici + verdetto. NON esegue merge né scrive: l\'agente principale (single-writer) crea il branch di integrazione, mergia con i gate per-step, build+test, invoca sdlc-verifier e promuove a main solo su conferma (mai --force).',
  phases: [
    { title: 'Overlap', detail: 'analisi read-only per Piano: file/entità/enum/contratti toccati' },
    { title: 'Order', detail: 'proposta ordine impact/conflict-aware + conflitti semantici' },
    { title: 'Critic', detail: 'completeness-critic: nessun Piano/commit perso' },
  ],
}

// ---------------------------------------------------------------------------
// args (preparati dall'agente principale — vedi skill sdlc-merge):
//   plans:   [{slug, branches:[{sigla, branch, base}], commit_refs:[string], summary}]
//   repos:   [{nome, sigla, path, type}]
//   changelog_excerpt: string   (## Piani + attività per commit-ref, #3)
//   contracts_excerpt: string   (CONTRACTS.md per i conflitti semantici FE<->BE)
//   profile, const: oggetti | null
//   depth: 'standard'|'ultracode'   verifier_panel: number
// ---------------------------------------------------------------------------
const plans = (args && Array.isArray(args.plans)) ? args.plans : []
const repos = (args && Array.isArray(args.repos)) ? args.repos : []
const changelogExcerpt = (args && args.changelog_excerpt) || ''
const contractsExcerpt = (args && args.contracts_excerpt) || ''
const profile = args ? (args.profile || null) : null
const constJson = args ? (args.const || null) : null
const depth = (args && args.depth) ? args.depth : 'standard'
const panel = (args && Number(args.verifier_panel)) ? Number(args.verifier_panel) : 3

const OVERLAP_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    plan: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },        // path toccati (per repo/sigla prefissati)
    symbols: { type: 'array', items: { type: 'string' } },      // simboli/classi/funzioni toccati
    entities: { type: 'array', items: { type: 'string' } },     // entità/enum/DTO
    contracts: { type: 'array', items: { type: 'string' } },    // endpoint/API contract toccati
    notes: { type: 'string' },
  },
  required: ['plan', 'files', 'symbols', 'entities', 'contracts'],
}

const ORDER_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    order: { type: 'array', items: { type: 'string' } },        // slug dei Piani nell'ordine proposto
    rationale: { type: 'string' },
    semantic_conflicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          kind: { type: 'string', enum: ['symbol', 'api', 'entity', 'enum', 'file'] },
          ref: { type: 'string' },
          plans: { type: 'array', items: { type: 'string' } },
          description: { type: 'string' },
          suggestion: { type: 'string', enum: ['guided-resolution', 'remediation-task'] },
        },
        required: ['kind', 'ref', 'plans', 'description', 'suggestion'],
      },
    },
  },
  required: ['order', 'rationale', 'semantic_conflicts'],
}

const CRITIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    all_plans_covered: { type: 'boolean' },
    missing: { type: 'array', items: { type: 'string' } },      // Piani/commit non coperti dall'ordine
    risks: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['all_plans_covered', 'missing', 'risks'],
}

function reposBlock() {
  return repos.map(r => `  - ${r.sigla} (${r.type || '?'}): ${r.path}`).join('\n') || '  (nessun repo fornito)'
}
function ctxBlock() {
  let s = ''
  if (profile) s += `PROFILE.json: ${JSON.stringify(profile).slice(0, 3000)}\n`
  if (constJson) s += `CONST.json: ${JSON.stringify(constJson).slice(0, 2000)}\n`
  return s
}

function buildOverlapPrompt(p) {
  return `Sei sdlc-codebase-explorer in SOLA LETTURA. Analizza cosa TOCCA il Piano [${p.slug}] nei repo di codice, per l'overlap analysis di un'integrazione cross-piano. NON modificare nulla, NON eseguire merge.

Branch del Piano (per repo): ${(p.branches || []).map(b => `${b.sigla}:${b.branch} (base ${b.base || 'main'})`).join(', ') || '(non forniti)'}
Commit-ref (dal changelog): ${(p.commit_refs || []).join(', ') || '(non forniti)'}
Sintesi Piano: ${p.summary || ''}

Repo di codice (read-only):
${reposBlock()}

${ctxBlock()}${contractsExcerpt ? `CONTRACTS.md (per gli endpoint/API toccati):\n${contractsExcerpt.slice(0, 3000)}\n` : ''}
Elenca, per questo Piano: i FILE toccati (prefissa con la sigla del repo), i SIMBOLI (classi/funzioni), le ENTITÀ/enum/DTO, e gli endpoint/API-contract toccati. Usa i branch/commit come guida (`git diff <base>..<branch>` concettualmente); se non puoi diffare, deduci dal codice del branch. Sii preciso: questi dati alimentano il rilevamento dei conflitti.`
}

function buildOrderPrompt(overlaps) {
  return `Sei un analista di integrazione cross-piano. Dato l'overlap di N Piani, proponi l'ORDINE di merge che MINIMIZZA i conflitti e rispetta le dipendenze cross-piano, e RILEVA i conflitti SEMANTICI (modifiche incompatibili allo stesso simbolo/API/entità/enum/file).

Overlap per Piano:
${JSON.stringify(overlaps).slice(0, 12000)}

${changelogExcerpt ? `Changelog (cosa ha prodotto ogni Piano):\n${changelogExcerpt.slice(0, 3000)}\n` : ''}${contractsExcerpt ? `CONTRACTS.md (conflitti API FE<->BE):\n${contractsExcerpt.slice(0, 2500)}\n` : ''}
Rispondi con: order (slug dei Piani nell'ordine proposto), rationale (perché quest'ordine minimizza i conflitti + dipendenze), semantic_conflicts (per ogni sovrapposizione incompatibile: kind, ref, plans coinvolti, description, suggestion ∈ {guided-resolution, remediation-task}). Un conflitto puramente testuale sullo stesso file NON è semantico se le modifiche sono compatibili — segnala solo le incompatibilità reali.`
}

function buildAdvPrompt(sc, k) {
  return `Sei un verificatore scettico (#${k + 1}) di un CONFLITTO SEMANTICO proposto in un'integrazione cross-piano. SOLA LETTURA. Conferma o refuta che sia un vero conflitto incompatibile.

Conflitto: kind=${sc.kind}, ref=${sc.ref}, plans=${(sc.plans || []).join('+')}
Descrizione: ${sc.description}
Repo:
${reposBlock()}
Refuta (confirmed=false) se le due modifiche sono in realtà COMPATIBILI (nessuna rottura di simbolo/API/entità/enum). Conferma (confirmed=true) se integrarle romperebbe il comportamento o l'API. In dubbio → confirmed=true (meglio evidenziarlo). Verdetto sul singolo conflitto.`
}

const ADV_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { ref: { type: 'string' }, confirmed: { type: 'boolean' }, reason: { type: 'string' } },
  required: ['ref', 'confirmed', 'reason'],
}

// ---------------------------------------------------------------------------
if (plans.length < 1) {
  log('Nessun Piano in args.plans — niente da integrare.')
  return { meta_run: { plans: 0 }, overlaps: [], order: [], semantic_conflicts: [], completeness: { all_plans_covered: true, missing: [], risks: [] } }
}

// Fase 1 — overlap analysis parallela (barrier: serve la vista completa per l'ordine).
phase('Overlap')
log(`Overlap analysis di ${plans.length} Piani su ${repos.length} repo (depth=${depth}).`)
const overlaps = (await parallel(plans.map(p => () =>
  agent(buildOverlapPrompt(p), { label: `overlap:${p.slug}`, phase: 'Overlap', agentType: 'sdlc-codebase-explorer', schema: OVERLAP_SCHEMA })
))).filter(Boolean)

// Fase 2 — ordine impact-aware + conflitti semantici.
phase('Order')
const orderRes = await agent(buildOrderPrompt(overlaps), { label: 'order:impact-aware', phase: 'Order', schema: ORDER_SCHEMA })
  || { order: plans.map(p => p.slug), rationale: 'fallback: ordine di input', semantic_conflicts: [] }

// adversarial-verify dei conflitti semantici (panel scettico) — tiene solo quelli confermati.
let confirmedConflicts = orderRes.semantic_conflicts || []
if (confirmedConflicts.length) {
  const checked = await parallel(confirmedConflicts.map(sc => () =>
    parallel(Array.from({ length: panel }, (_u, k) => () =>
      agent(buildAdvPrompt(sc, k), { label: `adv:${sc.ref}#${k + 1}`, phase: 'Order', schema: ADV_SCHEMA })))
      .then(votes => {
        const v = votes.filter(Boolean)
        const yes = v.filter(x => x.confirmed).length
        return { sc, confirmed: yes * 2 >= v.length, votes: v.length }   // dubbio → confermato (>=)
      })
  ))
  confirmedConflicts = checked.filter(Boolean).filter(c => c.confirmed).map(c => c.sc)
}

// Fase 3 — completeness-critic (barrier).
phase('Critic')
const critic = await agent(
  `Sei un completeness-critic di un'integrazione cross-piano. SOLA LETTURA.\nPiani da integrare: ${plans.map(p => p.slug).join(', ')}\nOrdine proposto: ${(orderRes.order || []).join(' → ')}\nOverlap: ${JSON.stringify(overlaps).slice(0, 6000)}\nVerifica: (1) all_plans_covered = l'ordine include TUTTI i Piani (nessuno perso); (2) missing = Piani/commit non coperti; (3) risks = rischi residui (commit persi, dipendenze non rispettate, conflitti non evidenziati). Sii esaustivo.`,
  { label: 'critic:completeness', phase: 'Critic', schema: CRITIC_SCHEMA }
) || { all_plans_covered: true, missing: [], risks: [] }

log(`Integrazione: ordine [${(orderRes.order || []).join(' → ')}], ${confirmedConflicts.length} conflitti semantici confermati, all_plans_covered=${critic.all_plans_covered}.`)

// NIENTE merge/scrittura: l'agente principale crea il branch di integrazione, mergia con i gate,
// build+test per repo, invoca sdlc-verifier, promuove a main solo su conferma (mai --force),
// scrive INTEGRATION.md + entry ⇄ MERGE nel changelog (single-writer).
return {
  meta_run: { plans: plans.length, repos: repos.length, depth, panel },
  overlaps,
  order: orderRes.order || [],
  order_rationale: orderRes.rationale || '',
  semantic_conflicts: confirmedConflicts,
  completeness: critic,
}
