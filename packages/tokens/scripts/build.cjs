#!/usr/bin/env node
/**
 * Spiro tokens build script
 *
 * Reads src/figma-import.json (the single source of truth) and emits:
 *   dist/tokens.css           — CSS custom properties for :root + [data-theme=dark]
 *   dist/tokens.js            — flat ESM constants
 *   dist/tokens.cjs           — CommonJS variant
 *   dist/tokens.d.ts          — typed exports
 *   dist/tokens.json          — W3C Design Tokens spec format
 *   dist/tailwind.preset.cjs  — Tailwind v3 preset
 */

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const SRC  = path.join(ROOT, 'src', 'figma-import.json');
const OUT  = path.join(ROOT, 'dist');

if (!fs.existsSync(SRC)) {
  console.error(`Missing source: ${SRC}`);
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

const data = JSON.parse(fs.readFileSync(SRC, 'utf8'));

// ----- helpers -----------------------------------------------------------

const kebab = (s) =>
  String(s)
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\/_\s]+/g, '-')
    .toLowerCase();

const camel = (s) => {
  const parts = kebab(s).split('-').filter(Boolean);
  if (!parts.length) return '';
  return parts[0] + parts.slice(1).map((w) => w[0].toUpperCase() + w.slice(1)).join('');
};

const cssVar = (name) => `--spiro-${kebab(name)}`;

const cssRgba = ({ r, g, b, a = 1 }) => {
  const c = (n) => Math.round(n * 255);
  const aRound = Number(a.toFixed(3));
  return `rgba(${c(r)},${c(g)},${c(b)},${aRound})`;
};

const rgbaToHex = ({ r, g, b, a = 1 }) => {
  const h = (n) => Math.round(n * 255).toString(16).padStart(2, '0').toUpperCase();
  const alpha = a < 1 ? h(a) : '';
  return `#${h(r)}${h(g)}${h(b)}${alpha}`;
};

const valueFor = (variable, mode) => variable.valuesByMode?.[mode];

// ----- step 1: read collections -----------------------------------------

const colorCollection = data.collections.find((c) => c.name === 'Spiro Color');
const colorVarsLight  = {};
const colorVarsDark   = {};
const numberMaps = {};

for (const variable of colorCollection.variables) {
  const cssName = cssVar(variable.name);
  const lightVal = valueFor(variable, 'Light');
  const darkVal  = valueFor(variable, 'Dark') ?? lightVal;
  const norm = (v) => (typeof v === 'string' ? v : v ? rgbaToHex(v) : null);
  const l = norm(lightVal);
  const d = norm(darkVal);
  if (l) {
    colorVarsLight[cssName] = l;
    colorVarsDark[cssName]  = d;
  }
}

for (const c of data.collections) {
  if (c.name === 'Spiro Color') continue;
  const map = {};
  for (const v of c.variables) {
    const segs = v.name.split('/');
    const key = segs.slice(1).join('-');
    map[key] = valueFor(v, 'Default');
  }
  numberMaps[c.name] = map;
}

// radius pill is a special name → 9999px
const radiusValue = (key, raw) =>
  String(key).toLowerCase().includes('pill') ? '9999px' : `${raw}px`;

// ----- step 2: write tokens.css -----------------------------------------

const cssLines = [];
cssLines.push('/*');
cssLines.push(` * Spiro Design Tokens — v${data.version}`);
cssLines.push(' * Auto-generated from figma-import.json. Do not edit by hand.');
cssLines.push(' */');
cssLines.push('');
cssLines.push(':root {');
cssLines.push('  /* ---------- Color ---------- */');
for (const [k, v] of Object.entries(colorVarsLight)) cssLines.push(`  ${k}: ${v};`);

cssLines.push('');
cssLines.push('  /* ---------- Spacing ---------- */');
for (const [k, v] of Object.entries(numberMaps['Spiro Spacing'] || {})) {
  cssLines.push(`  --spiro-space-${k}: ${v}px;`);
}
cssLines.push('');
cssLines.push('  /* ---------- Radius ---------- */');
for (const [k, v] of Object.entries(numberMaps['Spiro Radius'] || {})) {
  cssLines.push(`  --spiro-radius-${k}: ${radiusValue(k, v)};`);
}
cssLines.push('');
cssLines.push('  /* ---------- Stroke ---------- */');
for (const [k, v] of Object.entries(numberMaps['Spiro Stroke'] || {})) {
  cssLines.push(`  --spiro-border-${k}: ${v}px;`);
}
cssLines.push('');
cssLines.push('  /* ---------- Opacity ---------- */');
for (const [k, v] of Object.entries(numberMaps['Spiro Opacity'] || {})) {
  cssLines.push(`  --spiro-opacity-${k}: ${(Number(v) / 100).toFixed(2)};`);
}

cssLines.push('');
cssLines.push('  /* ---------- Typography ---------- */');
cssLines.push(`  --spiro-font-display: 'Clash Grotesk', 'Inter', system-ui, sans-serif;`);
cssLines.push(`  --spiro-font-sans: 'DM Sans', 'Inter', system-ui, sans-serif;`);
cssLines.push(`  --spiro-font-handwritten: 'Kalam', cursive;`);

cssLines.push('');
cssLines.push('  /* ---------- Motion ---------- */');
cssLines.push(`  --spiro-duration-fast: 120ms;`);
cssLines.push(`  --spiro-duration-base: 200ms;`);
cssLines.push(`  --spiro-duration-slow: 320ms;`);
cssLines.push(`  --spiro-easing-standard: cubic-bezier(0.2, 0, 0, 1);`);
cssLines.push(`  --spiro-easing-enter: cubic-bezier(0, 0, 0.2, 1);`);
cssLines.push(`  --spiro-easing-exit: cubic-bezier(0.4, 0, 1, 1);`);

// shadows from effectStyles
const shadowsLight = {};
for (const e of (data.effectStyles || [])) {
  if (!e.name.startsWith('shadow/')) continue;
  const key = e.name.replace('shadow/', '');
  const parts = e.effects.map((fx) => {
    const inset = fx.type === 'INNER_SHADOW' ? 'inset ' : '';
    const color = fx.color ? cssRgba(fx.color) : 'rgba(0,0,0,0.10)';
    const x = fx.offset?.x ?? 0;
    const y = fx.offset?.y ?? 0;
    return `${inset}${x}px ${y}px ${fx.radius || 0}px ${fx.spread || 0}px ${color}`;
  }).join(', ');
  shadowsLight[key] = parts;
}
const darkShadowOverrides = {
  'xs': '0 1px 2px 0 rgba(0,0,0,0.40)',
  'sm': '0 1px 3px 0 rgba(0,0,0,0.50), 0 1px 2px -1px rgba(0,0,0,0.40)',
  'md': '0 4px 8px -1px rgba(0,0,0,0.55), 0 2px 4px -2px rgba(0,0,0,0.40)',
  'lg': '0 10px 20px -3px rgba(0,0,0,0.60), 0 4px 8px -4px rgba(0,0,0,0.45)',
  'xl': '0 20px 30px -5px rgba(0,0,0,0.65), 0 8px 12px -6px rgba(0,0,0,0.40)',
  '2xl': '0 28px 56px -12px rgba(0,0,0,0.75)',
  'inner': 'inset 0 2px 4px 0 rgba(0,0,0,0.40)',
  'focus': '0 0 0 3px rgba(141,152,253,0.55)',
  'focus-danger': '0 0 0 3px rgba(248,113,113,0.55)',
};

cssLines.push('');
cssLines.push('  /* ---------- Shadow (light) ---------- */');
for (const [k, v] of Object.entries(shadowsLight)) cssLines.push(`  --spiro-shadow-${k}: ${v};`);
cssLines.push('}');
cssLines.push('');
cssLines.push(`[data-theme='dark'] {`);
cssLines.push('  /* ---------- Color (dark) ---------- */');
for (const [k, v] of Object.entries(colorVarsDark)) {
  if (colorVarsLight[k] !== v) cssLines.push(`  ${k}: ${v};`);
}
cssLines.push('');
cssLines.push('  /* ---------- Shadow (dark) ---------- */');
for (const [k, v] of Object.entries(darkShadowOverrides)) {
  if (shadowsLight[k]) cssLines.push(`  --spiro-shadow-${k}: ${v};`);
}
cssLines.push('}');

fs.writeFileSync(path.join(OUT, 'tokens.css'), cssLines.join('\n') + '\n');
console.log('  wrote dist/tokens.css');

// ----- step 3: tokens.json (W3C Design Tokens format) ------------------

const w3c = {
  $description: `Spiro Design Tokens v${data.version}`,
  color: {},
  spacing: {},
  radius: {},
  border: {},
  opacity: {},
  shadow: {},
};

const setNested = (root, segments, value, type) => {
  let node = root;
  for (let i = 0; i < segments.length - 1; i++) {
    if (!node[segments[i]] || node[segments[i]].$value !== undefined) {
      node[segments[i]] = node[segments[i]] || {};
    }
    node = node[segments[i]];
  }
  node[segments[segments.length - 1]] = { $value: value, $type: type };
};

for (const variable of colorCollection.variables) {
  const segs = variable.name.split('/');
  const v = valueFor(variable, 'Light');
  const value = typeof v === 'string' ? v : (v ? rgbaToHex(v) : '#000');
  setNested(w3c.color, segs, value, 'color');
}
for (const [k, v] of Object.entries(numberMaps['Spiro Spacing'] || {})) {
  w3c.spacing[k] = { $value: `${v}px`, $type: 'dimension' };
}
for (const [k, v] of Object.entries(numberMaps['Spiro Radius'] || {})) {
  w3c.radius[k] = { $value: radiusValue(k, v), $type: 'dimension' };
}
for (const [k, v] of Object.entries(numberMaps['Spiro Stroke'] || {})) {
  w3c.border[k] = { $value: `${v}px`, $type: 'dimension' };
}
for (const [k, v] of Object.entries(numberMaps['Spiro Opacity'] || {})) {
  w3c.opacity[k] = { $value: Number((Number(v) / 100).toFixed(2)), $type: 'number' };
}
for (const [k, v] of Object.entries(shadowsLight)) {
  w3c.shadow[k] = { $value: v, $type: 'shadow' };
}

fs.writeFileSync(path.join(OUT, 'tokens.json'), JSON.stringify(w3c, null, 2));
console.log('  wrote dist/tokens.json');

// ----- step 4: tokens.js / tokens.cjs / tokens.d.ts --------------------

const flat = {};
for (const variable of colorCollection.variables) {
  const v = valueFor(variable, 'Light');
  const value = typeof v === 'string' ? v : (v ? rgbaToHex(v) : '#000');
  flat[camel('color/' + variable.name)] = value;
}
for (const [k, v] of Object.entries(numberMaps['Spiro Spacing'] || {})) flat[camel('space/' + k)] = `${v}px`;
for (const [k, v] of Object.entries(numberMaps['Spiro Radius'] || {})) flat[camel('radius/' + k)] = radiusValue(k, v);
for (const [k, v] of Object.entries(numberMaps['Spiro Stroke'] || {})) flat[camel('border/' + k)] = `${v}px`;
for (const [k, v] of Object.entries(shadowsLight)) flat[camel('shadow/' + k)] = v;

fs.writeFileSync(
  path.join(OUT, 'tokens.js'),
  [
    `// Spiro tokens v${data.version} — flat ESM constants. Auto-generated.`,
    `export const tokens = ${JSON.stringify(flat, null, 2)};`,
    `export default tokens;`,
    ``,
  ].join('\n')
);
fs.writeFileSync(
  path.join(OUT, 'tokens.cjs'),
  `// Spiro tokens v${data.version} — flat CommonJS constants. Auto-generated.\nmodule.exports = ${JSON.stringify(flat, null, 2)};\n`
);
fs.writeFileSync(
  path.join(OUT, 'tokens.d.ts'),
  [
    `// Auto-generated types for @aslicopper/tokens v${data.version}`,
    `export interface SpiroTokens {`,
    ...Object.keys(flat).map((k) => `  ${JSON.stringify(k)}: string;`),
    `}`,
    `export declare const tokens: SpiroTokens;`,
    `export default tokens;`,
    ``,
  ].join('\n')
);
console.log('  wrote dist/tokens.{js,cjs,d.ts}');

// ----- step 5: tailwind preset ------------------------------------------

const colorTree = (() => {
  const t = {};
  for (const variable of colorCollection.variables) {
    const segs = variable.name.split('/');
    let node = t;
    for (let i = 0; i < segs.length - 1; i++) {
      if (typeof node[segs[i]] === 'string') break;
      node[segs[i]] = node[segs[i]] || {};
      node = node[segs[i]];
    }
    node[segs[segs.length - 1]] = `var(${cssVar(variable.name)})`;
  }
  return t;
})();

const spacingScale = {};
for (const [k, v] of Object.entries(numberMaps['Spiro Spacing'] || {})) spacingScale[k] = `${v}px`;
const radiusScale = {};
for (const [k, v] of Object.entries(numberMaps['Spiro Radius'] || {})) radiusScale[k] = radiusValue(k, v);
const borderScale = {};
for (const [k, v] of Object.entries(numberMaps['Spiro Stroke'] || {})) borderScale[k] = `${v}px`;
const shadowScale = {};
for (const k of Object.keys(shadowsLight)) shadowScale[k] = `var(--spiro-shadow-${k})`;

const presetLines = [
  `// Tailwind v3+ preset for the Spiro Design System.`,
  `// Auto-generated from figma-import.json v${data.version}.`,
  `// Usage:`,
  `//   const spiro = require('@aslicopper/tokens/tailwind');`,
  `//   module.exports = { presets: [spiro], content: [...] };`,
  ``,
  `module.exports = {`,
  `  theme: {`,
  `    extend: {`,
  `      colors: ${JSON.stringify(colorTree, null, 8).replace(/\n/g, '\n      ')},`,
  `      spacing: ${JSON.stringify(spacingScale, null, 8).replace(/\n/g, '\n      ')},`,
  `      borderRadius: ${JSON.stringify(radiusScale, null, 8).replace(/\n/g, '\n      ')},`,
  `      borderWidth: ${JSON.stringify(borderScale, null, 8).replace(/\n/g, '\n      ')},`,
  `      boxShadow: ${JSON.stringify(shadowScale, null, 8).replace(/\n/g, '\n      ')},`,
  `      fontFamily: {`,
  `        display: ['Clash Grotesk', 'Inter', 'system-ui', 'sans-serif'],`,
  `        sans: ['DM Sans', 'Inter', 'system-ui', 'sans-serif'],`,
  `        handwritten: ['Kalam', 'cursive'],`,
  `      },`,
  `      transitionDuration: {`,
  `        fast: '120ms',`,
  `        DEFAULT: '200ms',`,
  `        slow: '320ms',`,
  `      },`,
  `      transitionTimingFunction: {`,
  `        standard: 'cubic-bezier(0.2, 0, 0, 1)',`,
  `        enter: 'cubic-bezier(0, 0, 0.2, 1)',`,
  `        exit: 'cubic-bezier(0.4, 0, 1, 1)',`,
  `      },`,
  `    },`,
  `  },`,
  `};`,
  ``,
];
fs.writeFileSync(path.join(OUT, 'tailwind.preset.cjs'), presetLines.join('\n'));
console.log('  wrote dist/tailwind.preset.cjs');

console.log(`\nSpiro tokens v${data.version} built →`, path.relative(process.cwd(), OUT));
