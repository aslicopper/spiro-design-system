# Spiro Design System

Single source of truth for the Spiro brand — colors, typography, spacing, shadows, gradients, and 14 components — distributed as npm packages, a Figma plugin, and W3C-spec JSON.

## Packages

| Package                | What                                                             |
| ---------------------- | ---------------------------------------------------------------- |
| **`@aslicopper/tokens`**    | CSS variables, JS/TS constants, W3C tokens.json, Tailwind preset |
| **`@aslicopper/react`**     | React components (`Button`, more coming) styled with the tokens  |
| **`@aslicopper/figma-plugin`** | Plugin .zip that imports the system into Figma Variables + Styles + Components |

All three read from the same `figma-import.json`. One edit propagates to code, Figma, and W3C tools.

## Install

Spiro uses **GitHub Packages** as the private npm registry. Each consumer repo needs a one-time setup:

```bash
# .npmrc — at the root of any repo that consumes @aslicopper packages
@aslicopper:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NPM_TOKEN}
```

Then `NPM_TOKEN` is a GitHub PAT with `read:packages` scope, set in each developer's shell or in CI as a secret.

```bash
npm install @aslicopper/tokens
npm install @aslicopper/react
```

See per-package READMEs for usage.

## Quick start (vanilla web)

```html
<link rel="stylesheet" href="https://unpkg.com/@aslicopper/tokens/dist/tokens.css" />
<button class="spiro-btn spiro-btn--primary spiro-btn--md">Swap battery</button>
```

(Replace `unpkg.com` with the GitHub Packages URL once published privately, or copy `tokens.css` into your repo for offline use.)

## Quick start (Tailwind)

```js
// tailwind.config.js
module.exports = {
  presets: [require('@aslicopper/tokens/tailwind')],
  content: ['./src/**/*.{ts,tsx,jsx,html}'],
};
```

```jsx
<button className="bg-accent-default text-fg-on-accent rounded-pill px-5 py-2 shadow-md">
  Swap battery
</button>
```

## Quick start (React)

```tsx
import '@aslicopper/tokens/css';      // tokens
import '@aslicopper/tokens/fonts';    // self-hosted Clash Grotesk + DM Sans + Kalam
import '@aslicopper/react/styles.css'; // component styles
import { Button } from '@aslicopper/react';

export const App = () => <Button variant="primary">Swap battery</Button>;
```

## Releasing

```
git tag v0.17.0 && git push --tags
```

The `Publish` GitHub Action builds every package, pushes to GitHub Packages, and attaches the Figma plugin .zip to the GitHub Release.

## Editing tokens

The source of truth is `packages/tokens/src/figma-import.json`. Edit it, run `npm run build:tokens`, commit. The Figma plugin reads the same file — designers re-run the plugin to pick up the same change.

## Repository layout

```
spiro-design-system/
├── packages/
│   ├── tokens/              # @aslicopper/tokens
│   │   ├── src/figma-import.json   ← single source of truth
│   │   ├── scripts/build.js
│   │   └── dist/            # generated: tokens.css/.js/.cjs/.json/.d.ts + tailwind preset
│   ├── react/               # @aslicopper/react
│   │   └── src/Button/
│   └── figma-plugin/        # @aslicopper/figma-plugin
│       └── spiro-figma-importer.zip
├── .github/workflows/publish.yml
└── package.json             # npm workspaces root
```

## Contributing

1. Open a PR that changes `packages/tokens/src/figma-import.json` (or a component file).
2. CI runs `npm run build` to verify everything compiles and the W3C JSON, CSS, Tailwind preset, and types regenerate cleanly.
3. After merge, bump the relevant package version with `npm version` and push a tag — the Publish workflow does the rest.

Versioning is semver: token value change = patch, new token = minor, rename or removal = major (with a deprecation alias for one minor version before deletion).
