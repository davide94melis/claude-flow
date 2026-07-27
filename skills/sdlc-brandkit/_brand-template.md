# Brand kit — <PROJECT> (<domain>)

> Design contract for the Mockup Designer. HIGH-FIDELITY: derive every token/component/page
> from this file VERBATIM. Do not invent colors, spacing, or type. Anchor to the reference
> screenshots in assets/screenshots/.

## 1. Meta
- Project: <name> · Stack: <detected stack> · UI library: <lib + version>
- Source commit: <short-sha> · Generated: <YYYY-MM-DD> by sdlc-brandkit
- Token sources: <repo-relative paths / DOM> · Fidelity target: quasi-pixel-perfect (AA)
> PATHS: usa solo path relativi al repo (strip del prefisso repo-root) e SHA corti. MAI path assoluti locali — POSIX (`/Users/...`), `file://`, Windows (`C:\...`, `file:///C:/...`), UNC (`\\host\share`).

## 2. Design tokens
See `tokens.css` (inline it verbatim in every mockup) — it is the SINGLE SOURCE of token values.
> The "notable values" summary table is OPTIONAL. If present it MUST be auto-generated from `tokens.css`
> (never hand-maintained) to prevent drift (e.g. `#2c8287` vs `#14b8a6`).
<key tokens table — AUTO-GENERATED from tokens.css; do not hand-edit>

## 3. Base / reset CSS
```css
<the reset + app compensations the real app uses>
```

## 4. Components
For each component: anatomy, variants, states (default/hover/focus/active/disabled/invalid),
sizing, and a copy-paste snippet in `assets/snippets/<component>.html`.
<component list + per-component notes>

## 5. Pages / layouts
Recurring page shells (snippets in assets/snippets/pages/):
<page list>

## 6. Reference screenshots
Golden references in `assets/screenshots/` (see `assets/screenshots/manifest.json`):
<screen -> file table>

## 7. Fidelity directives (Do / Don't)
- DO inline tokens.css verbatim; DO reuse component snippets; DO anchor to screenshots.
- DON'T invent colors/spacing/type; DON'T restyle the visual grammar; DON'T drift from the scale.

## 8. Locale & accessibility
- UI language: <lang>. Target: WCAG 2.1 AA.
- PALETTE LOCKED: contrast remediations must stay within the brand ramps or be flagged as a
  brand-level decision — never silently override brand colors.
