# @aslicopper/preview

The visual preview site for the Spiro Design System. A single-file HTML page that renders every token, typography role, shadow, gradient, component, icon, and pattern from the design system. Useful for designers reviewing visual decisions, engineers picking the right CSS variable, and AI design tools that need a faithful reference.

## Build

```bash
cd packages/preview
npm run build
```

This runs `python3 scripts/build.py`, which:

1. Reads tokens from `../tokens/dist/tokens.css`
2. Reads font declarations from `../tokens/dist/fonts.css`
3. Reads Button styles from `../react/src/Button/Button.css`
4. Renders the assembled page to `dist/index.html`
5. Copies the WOFF2 fonts from `../tokens/dist/fonts/` next to the output so `@font-face` URLs resolve

Output is roughly 290 KB. Open `dist/index.html` in any browser, or use `npm run serve` (defaults to <http://localhost:8080>) for live preview.

## Auto-deploy to GitHub Pages

Every push to `main` that touches `packages/preview/**` or `packages/tokens/dist/**` triggers the **Deploy preview** workflow. After it runs, the latest site is live at:

<https://aslicopper.github.io/spiro-design-system/>

## Edit the site

The build script (`scripts/build.py`) is monolithic — about 2,400 lines of Python that emit a fully inlined HTML document. Major sections:

- Hero — navy/blue gradient band with logo, title, stat pills
- Color primitives — 15 ramps × 13 steps
- Typography — 28 text styles, font family demo, letter-spacing notes
- Spacing / Radius / Borders / Shadows tables
- Tokens — semantic, decorative, gradient, in-context
- Components — masonry gallery of 14 components
- Icons / Patterns — line icons + badges + decorative patterns
- Prompts — AI-generation prompt templates

To change a section, find its `def section_name()` or its inline HTML block (search the file for the section title) and edit. Re-run `npm run build` to regenerate.

## Source of design data

The preview reflects design tokens from `@aslicopper/tokens` (color/spacing/radius/etc.) and component CSS from `@aslicopper/react`. If a token changes upstream, rebuilding here automatically reflects it — but the rebuild is manual (or triggered by the deploy workflow on push to main).

## Why Python instead of Node?

Historical reason — the script was bootstrapped in Python because of better text-templating ergonomics for a one-off generator. There's no reason it couldn't be ported to Node/JS later if the rest of the repo's tooling consolidates. For now, Python 3.10+ with no external dependencies is the only requirement.
