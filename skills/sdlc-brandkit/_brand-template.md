# Brand kit — <PROJECT> (<domain>)

> Design contract for the Mockup Designer. HIGH-FIDELITY: derive every token/component/page
> from this file VERBATIM. Do not invent colors, spacing, or type. Anchor to the reference
> screenshots in assets/screenshots/.

## 1. Meta
- Project: <name> · Stack: <detected stack> · UI library: <lib + version>
- Source commit: <sha> · Generated: <YYYY-MM-DD> by sdlc-brandkit
- Token sources: <files / DOM> · Fidelity target: quasi-pixel-perfect (AA)

## 2. Design tokens
See `tokens.css` (inline it verbatim in every mockup). Summary of the notable values:
<key tokens table>

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
