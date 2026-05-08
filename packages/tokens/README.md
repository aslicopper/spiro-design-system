# @aslicopper/tokens

Single source of truth for the Spiro Design System. Ships as CSS variables, ESM/CJS constants, TypeScript types, a W3C Design Tokens spec JSON, and a Tailwind preset — all generated from one `figma-import.json`.

## Install

```bash
npm install @aslicopper/tokens
# or
pnpm add @aslicopper/tokens
```

(See the root `README.md` for registry setup.)

## Usage

### CSS variables (any framework)

```js
import '@aslicopper/tokens/css';
```

Then use the variables anywhere:

```css
.card {
  background: var(--spiro-bg-canvas);
  color: var(--spiro-fg-default);
  border: var(--spiro-border-1) solid var(--spiro-border-default);
  border-radius: var(--spiro-radius-12);
  box-shadow: var(--spiro-shadow-md);
}
```

Toggle dark mode by setting `data-theme="dark"` on `<html>`.

### Fonts

The Spiro typefaces (Clash Grotesk, DM Sans, Kalam) ship with the package as self-hosted WOFF2 files. One import wires up all eight `@font-face` declarations:

```js
import '@aslicopper/tokens/fonts';
```

Or pull them from a CDN instead — see comments at the top of `fonts.css` for the Fontshare + Google Fonts URLs. (Don't load both — pick one.)

All three families are licensed under the [SIL Open Font License](https://scripts.sil.org/OFL), so redistribution is fine.

### Tailwind preset

```js
// tailwind.config.js
module.exports = {
  presets: [require('@aslicopper/tokens/tailwind')],
  content: ['./src/**/*.{ts,tsx,jsx,html}'],
};
```

Then use Tailwind utilities backed by Spiro tokens:

```jsx
<button className="bg-accent-default text-fg-on-accent rounded-pill shadow-md px-5 py-2">
  Swap battery
</button>
```

### Typed constants

```ts
import { tokens } from '@aslicopper/tokens';

const styles = {
  background: tokens.colorBgCanvas,
  color: tokens.colorFgDefault,
};
```

### W3C / Tokens Studio JSON

For ingestion by Tokens Studio, Penpot, Style Dictionary, Claude Design, etc.:

```ts
import tokensJson from '@aslicopper/tokens/json';
```

The file follows the [W3C Design Tokens Community Group spec](https://www.w3.org/community/design-tokens/) — every leaf is `{ $value, $type }`.

## Building

The dist files are built from `src/figma-import.json`:

```bash
npm run build
```

Edit `src/figma-import.json`, run `npm run build`, commit both. The Figma plugin (in `@aslicopper/figma-plugin`) reads the same source file to update the Figma library.

## Contents

| Export                | What it is                                    |
| --------------------- | --------------------------------------------- |
| `@aslicopper/tokens`       | Flat ESM constants (`tokens.colorBgCanvas`)   |
| `@aslicopper/tokens/css`   | `tokens.css` — drop into any web project      |
| `@aslicopper/tokens/fonts` | `fonts.css` + 8 self-hosted WOFF2 files (~412KB total) |
| `@aslicopper/tokens/json`  | W3C-spec `tokens.json`                         |
| `@aslicopper/tokens/tailwind` | Tailwind v3+ preset                       |
| `@aslicopper/tokens/source` | Raw `figma-import.json` (for tooling)        |
