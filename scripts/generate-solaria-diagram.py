"""
Wave 4.4 — Genera SOLARIA_SDLC_DIAGRAM.svg riallineato al nuovo flusso a
2 fasi composite (1a/b/c, 2a/b/c) con 6 sub-fasi, swimlane Team Funz/
Solaria/Team Tech, cartella dataset/, gates GO/NO-GO, label Git Trees API
per handoff.

Output: claude-flow/docs/SOLARIA_SDLC_DIAGRAM.svg
"""
from pathlib import Path

W, H = 1900, 980
LANE_LABEL_W = 180
COLS = 6
CONTENT_X = 200
COL_W = 280
BOX_W = 270
BOX_GAP = (COL_W - BOX_W) // 2  # 5

# X-start of each column (1a, 1b, 1c, 2a, 2b, 2c)
COL_X = [CONTENT_X + i * COL_W for i in range(COLS)]

LANE_Y = {
    "funz": 200,
    "solaria": 360,
    "tech": 520,
}
LANE_H = 150

PHASE1_COLOR = "#2a8ac9"   # blue (Fase 1)
PHASE2_COLOR = "#58a55c"   # green (Fase 2)
GATE_COLOR = "#ffc107"     # yellow highlight for gates
INACTIVE_FILL = "#f5f5f5"
INACTIVE_STROKE = "#bbb"

# Sub-fase definitions
SUBFASI = [
    {"id": "1a", "title": "Setup tecnico", "color": PHASE1_COLOR,
     "subtitle": "GitHub repo + plans/ + CONST + PROFILE"},
    {"id": "1b", "title": "Setup dataset", "color": PHASE1_COLOR,
     "subtitle": "dataset/ Solaria (branding, glossario, ...)"},
    {"id": "1c", "title": "Authoring AFU", "color": PHASE1_COLOR,
     "subtitle": "FunctionalWeaver → Reviewer (GO/NO-GO) → review/clarify → Mockup → Playbook → handoff"},
    {"id": "2a", "title": "Implementazione", "color": PHASE2_COLOR,
     "subtitle": "(reviewer/clarify opz) → analyzer → executor → progress-report"},
    {"id": "2b", "title": "Update mid-flight", "color": PHASE2_COLOR,
     "subtitle": "(opzionale) Solaria F1c v2.0 → sdlc-updater"},
    {"id": "2c", "title": "Test e chiusura", "color": PHASE2_COLOR,
     "subtitle": "(a) tech tests → (b) func playbook → debug → done/"},
]

# Content per lane × column
# None = inactive
CONTENT = {
    "funz": [
        None,
        ["• Fornisce a Solaria branding, asset corporate, glossario, attori, perimetro",
         "• Solaria classifica e indicizza nel <b>dataset/</b>"],
        ["• Porta materiale offline (note, mail, mockup grezzi)",
         "• Rivede AFU prodotta dal FunctionalWeaver",
         "• Risponde a rilievi review/clarify post-GO",
         "• Porta AFU+mockup allo stakeholder per validazione (offline)"],
        ["(<i>solo Q&amp;A se review tech opzionale attivata in F2a</i>)"],
        ["• Raccoglie nuovi requisiti stakeholder",
         "• Arricchisce dataset del plan → rilancia F1c per AFU v2.0"],
        ["• Esegue manualmente il <b>playbook test</b> (md/xlsx) generato da Solaria in F1c",
         "• Annota fallimenti → Excel bug (<b>origine=funzionale</b>)"],
    ],
    "solaria": [
        ["(<i>non attivo</i>)"],
        ["<b>Crea dataset di progetto</b>",
         "• Upload + classificazione asset funzionali/branding",
         "• Sincronizzazione continua via GitHub Contents API su <code>dataset/</code>"],
        ["<b>Multi-agent authoring</b>",
         "• <b>FunctionalWeaver</b>: genera AFU dal dataset (no Q&amp;A)",
         "• <b>FunctionalReviewer</b>: gate <b style='background:#ffc107;padding:0 4px;'>GO/NO-GO</b> + coverage %",
         "• Skill <b>review/clarify</b> forkate (post-GO): corner case, bad flow",
         "• <b>Mockup Designer Agent</b>: mockups di esempio",
         "• <b>Playbook Generator</b>: tests/playbook.{md,xlsx}",
         "• <b>Handoff</b>: rename atomico draft→todo via <b>Git Trees API</b>"],
        ["(<i>opz: compila CLARIFY.md se review tech attivata</i>)",
         "• Detection commit [sdlc-reviewer]/[sdlc-clarify] via polling on-demand Commits API o webhook",
         "• Risposte funzionale → Contents API (commit [solaria-clarify])"],
        ["<b>Rigenera AFU v2.0</b>",
         "• Riusa FunctionalWeaver/Reviewer/Mockup/review-clarify/Playbook",
         "• afu-manifest: bump versione major + changelog"],
        ["(<i>passivo</i>)",
         "• Detection chiusura plan via polling/webhook",
         "• Notifica funzionale"],
    ],
    "tech": [
        ["<b>sdlc-profile-setup</b> (standalone)",
         "• Crea: <code>constitution/, references/, dataset/{scheletro}, plans/{draft,todo,in-progress,done}/</code>",
         "• Copia <code>afu-manifest.schema.json</code> v2"],
        ["(<i>non attivo</i>)"],
        ["(<i>non attivo</i> — Solaria autora; team tech consuma solo dopo handoff in F2a)"],
        ["<b>sdlc-reviewer + sdlc-clarify</b> (opzionali, TL decide)",
         "<b>sdlc-analyzer</b>: PLAN.md + TASKS.md (header processed_afu_version)",
         "<b>sdlc-executor</b>: implementa task + sposta in <code>in-progress/</code>",
         "<b>sdlc-progress-report</b>: PROGRESS.xlsx"],
        ["<b>sdlc-updater</b>: detecta delta via manifest.versione vs processed_afu_version",
         "• Usa manifest.changelog come fonte primaria",
         "• Aggiorna PLAN.md + TASKS.md preservando PROGRESS"],
        ["<b>(a) Test tecnici automatici</b> (unit/integration/perf/security)",
         "  → bug → <b>sdlc-debug</b> (origine=tecnico)",
         "<b>Gate</b>: test tecnici <b style='background:#ffc107;padding:0 4px;'>verdi</b> prima ondata (b)",
         "<b>sdlc-debug</b>: fix funzionali (origine=funzionale)",
         "<b>sdlc-executor</b>: chiusura automatica → <code>done/</code> se tutte task=Completata + bug_tec/func_aperti=0"],
    ],
}

ARTIFACTS = [
    ["<code>constitution/{CONST,PROFILE}.json</code>", "<code>afu-manifest.schema.json</code> v2",
     "Struttura <code>plans/{draft,todo,in-progress,done}/</code>"],
    ["<code>dataset/{branding,corporate,glossario.md,attori.md,perimetro.md}</code>",
     "Commit: <code>[solaria-dataset-*]</code>"],
    ["<code>plans/draft/&lt;plan&gt;/{requirements/{AFU.*, mockups/}, afu-manifest.json (coverage, gate=GO), REVIEW.md, tests/playbook.{md,xlsx}}</code>",
     "Handoff (Git Trees API): <code>[solaria-handoff]</code>"],
    ["<code>plans/todo/&lt;plan&gt;/{(opz) CLARIFY.md, PLAN.md, TASKS.md}</code>",
     "<code>plans/in-progress/&lt;plan&gt;/{PROGRESS.md, PROGRESS.xlsx}</code>"],
    ["<code>plans/in-progress/&lt;plan&gt;/{requirements/, afu-manifest.json v2, tests/playbook.* rigenerato}</code>",
     "Commit: <code>[solaria-update]</code>"],
    ["<code>plans/in-progress/&lt;plan&gt;/{bug-import-*.xlsx (colonna origine), BUG_REPORT.md (sez. tecnici + funzionali)}</code>",
     "<code>plans/done/&lt;plan&gt;/</code> (move automatico)"],
]


def chev(x, y, w, h, color, label, subtitle):
    """Chevron-style header box for sub-fase."""
    tip = 30
    pts = f"{x},{y} {x+w-tip},{y} {x+w},{y+h//2} {x+w-tip},{y+h} {x},{y+h} {x+tip},{y+h//2}"
    out = [
        f'<polygon points="{pts}" fill="{color}"/>',
        f'<text x="{x+w//2}" y="{y+18}" text-anchor="middle" fill="white" font-weight="700" font-size="14">{label}</text>',
        f'<foreignObject x="{x+10}" y="{y+22}" width="{w-20}" height="{h-22}">',
        f'  <div xmlns="http://www.w3.org/1999/xhtml" style="color:white; font-size:9.5px; text-align:center; line-height:1.2; padding-top:3px;">{subtitle}</div>',
        '</foreignObject>',
    ]
    return "\n".join(out)


def content_box(x, y, w, h, lines, color="#1f6fa3", lane=""):
    """White box with bullet content."""
    if lines is None or (len(lines) == 1 and "non attivo" in lines[0]):
        body = lines[0] if lines else "(non attivo)"
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{INACTIVE_FILL}" '
            f'stroke="{INACTIVE_STROKE}" stroke-width="1" stroke-dasharray="4,3" rx="8"/>\n'
            f'<foreignObject x="{x+10}" y="{y+h//2-15}" width="{w-20}" height="30">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-size:11px; color:#888; '
            f'line-height:1.3; text-align:center; font-style:italic;">{body}</div></foreignObject>'
        )
    html = "<br/>".join(f"• {l}" if not l.startswith(("<", "(")) else l for l in lines)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" '
        f'stroke="{color}" stroke-width="1.5" rx="8"/>\n'
        f'<foreignObject x="{x+10}" y="{y+8}" width="{w-20}" height="{h-12}">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-size:10.5px; color:#1a1a1a; '
        f'line-height:1.4;">{html}</div></foreignObject>'
    )


def lane_label(x, y, w, h, fill, lines):
    label = "\n".join(
        f'<text x="{x+w//2}" y="{y+25 + i*18}" text-anchor="middle" fill="white" '
        f'font-weight="700" font-size="13">{t}</text>'
        for i, t in enumerate(lines)
    )
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="4"/>\n{label}'


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial, sans-serif">',
    '<defs>',
    '  <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">',
    '    <polygon points="0,0 8,4 0,8" fill="#555"/>',
    '  </marker>',
    '</defs>',

    # Title
    '<text x="40" y="40" font-size="26" font-weight="700">Solaria ⇄ SDLC Skills</text>',
    '<text x="40" y="68" font-size="14">Nuovo flusso a <tspan font-weight="700">2 fasi composite</tspan> '
    '(Fase 1 Pre-Coding: 1a/1b/1c — Fase 2 Coding &amp; Test: 2a/2b/2c). '
    'Una repo Git per progetto, Solaria opera server-side via GitHub API.</text>',

    # Phase 1 wrapper banner
    f'<rect x="{COL_X[0]-5}" y="100" width="{3*COL_W+10}" height="30" fill="{PHASE1_COLOR}" opacity="0.15"/>',
    f'<text x="{COL_X[0]+3*COL_W//2}" y="120" text-anchor="middle" font-weight="700" '
    f'font-size="14" fill="{PHASE1_COLOR}">FASE 1 — PRE-CODING</text>',

    # Phase 2 wrapper banner
    f'<rect x="{COL_X[3]-5}" y="100" width="{3*COL_W+10}" height="30" fill="{PHASE2_COLOR}" opacity="0.15"/>',
    f'<text x="{COL_X[3]+3*COL_W//2}" y="120" text-anchor="middle" font-weight="700" '
    f'font-size="14" fill="{PHASE2_COLOR}">FASE 2 — CODING &amp; TEST</text>',
]

# Sub-fase chevron headers
for i, sf in enumerate(SUBFASI):
    parts.append(chev(COL_X[i]+5, 140, COL_W-10, 45, sf["color"],
                       f"{sf['id']} — {sf['title']}", sf["subtitle"]))

# Swimlanes
parts.append(f'<rect x="0" y="{LANE_Y["funz"]-5}" width="{W}" height="{LANE_H}" fill="#e0ecf5"/>')
parts.append(lane_label(20, LANE_Y["funz"]+30, 150, 70, "#2a8ac9",
                          ["TEAM", "FUNZIONALE"]))

parts.append(f'<rect x="0" y="{LANE_Y["solaria"]-5}" width="{W}" height="{LANE_H+50}" fill="#cfe1ee"/>')
parts.append(lane_label(20, LANE_Y["solaria"]+50, 150, 70, "#1f6fa3", ["SOLARIA"]))

parts.append(f'<rect x="0" y="{LANE_Y["tech"]+45}" width="{W}" height="{LANE_H+30}" fill="#e0ecf5"/>')
parts.append(lane_label(20, LANE_Y["tech"]+90, 150, 70, "#2a8ac9", ["TEAM", "TECH"]))

# Lane separators (dashed)
parts.append(f'<line x1="180" y1="{LANE_Y["solaria"]-10}" x2="{W}" y2="{LANE_Y["solaria"]-10}" '
              f'stroke="#888" stroke-dasharray="3,3"/>')
parts.append(f'<line x1="180" y1="{LANE_Y["tech"]+40}" x2="{W}" y2="{LANE_Y["tech"]+40}" '
              f'stroke="#888" stroke-dasharray="3,3"/>')

# Content boxes per (lane, sub-fase)
for i in range(COLS):
    x = COL_X[i] + BOX_GAP
    parts.append(content_box(x, LANE_Y["funz"]+10, BOX_W, 130, CONTENT["funz"][i], "#2a8ac9"))
    parts.append(content_box(x, LANE_Y["solaria"]+5, BOX_W, 180, CONTENT["solaria"][i], "#1f6fa3"))
    parts.append(content_box(x, LANE_Y["tech"]+55, BOX_W, 150, CONTENT["tech"][i], "#2a8ac9"))

# Artefatti row
art_y = LANE_Y["tech"] + 220
parts.append(f'<rect x="20" y="{art_y}" width="{W-40}" height="200" fill="#fafafa" stroke="#888" stroke-width="1.5" rx="4"/>')
parts.append(f'<rect x="40" y="{art_y+45}" width="130" height="60" fill="#9e9e9e" rx="4"/>')
parts.append(f'<text x="105" y="{art_y+72}" text-anchor="middle" fill="white" font-weight="700" font-size="12">ARTEFATTI</text>')
parts.append(f'<text x="105" y="{art_y+90}" text-anchor="middle" fill="white" font-weight="700" font-size="11">project_repo/</text>')

for i, art in enumerate(ARTIFACTS):
    x = COL_X[i] + BOX_GAP
    parts.append(content_box(x, art_y+30, BOX_W, 150, art, "#888"))

# Legend bottom
legend_y = art_y + 215
parts.append(f'<text x="40" y="{legend_y}" font-size="11" fill="#555">'
              '<tspan font-weight="700">Legenda:</tspan> '
              f'<tspan font-weight="700" fill="{PHASE1_COLOR}">■</tspan> Fase 1 (Pre-Coding) — '
              f'<tspan font-weight="700" fill="{PHASE2_COLOR}">■</tspan> Fase 2 (Coding &amp; Test) — '
              '<tspan style="background:#ffc107;padding:0 4px;">■</tspan> Quality gate (GO/NO-GO in F1c, '
              'test tecnici verdi in F2c) — Box tratteggiati = sub-fase non attiva per quella lane'
              '</text>')

parts.append('</svg>')

out = "\n".join(parts) + "\n"
Path(r"C:\Users\davmelis\Documents\MyGitHub\claude-flow\docs\SOLARIA_SDLC_DIAGRAM.svg").write_text(out, encoding="utf-8")
print(f"SVG written: {len(out)} chars, {out.count(chr(10))} lines")
