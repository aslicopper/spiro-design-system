# @aslicopper/react

Spiro Design System React components. Currently ships:

- `Button` — pill-shaped, six variants, three sizes, transient success state, full a11y.

More components will land here as they're promoted out of the Figma library.

## Install

```bash
npm install @aslicopper/react @aslicopper/tokens
```

## Usage

```tsx
import '@aslicopper/tokens/css';
import '@aslicopper/react/styles.css';

import { Button } from '@aslicopper/react';

export function App() {
  return <Button variant="primary" size="md">Swap battery</Button>;
}
```

## Theming

Spiro components are styled entirely with CSS custom properties from `@aslicopper/tokens`. To switch to dark mode:

```js
document.documentElement.setAttribute('data-theme', 'dark');
```

To rebrand: override the `--spiro-*` variables in your global stylesheet — components inherit instantly, no rebuild needed.

## Build

```bash
npm run build
```

Outputs `dist/index.{js,cjs,d.ts}` plus `dist/styles.css`.
