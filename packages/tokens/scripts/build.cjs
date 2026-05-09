#!/usr/bin/env node
/**
 * Spiro tokens build — reads Tokens Studio for Figma's tokens-studio.json
 * and emits the dist artifacts (CSS, JS, JSON, Tailwind preset, types).
 *
 * Tokens Studio organises tokens by "set" — one per Figma Variable Collection
 * + mode. Each set is a top-level key like "Spiro Color/Light", "Spiro
 * Spacing/Default". Leaf tokens follow the W3C Design Tokens spec:
 * { $type, $value, $extensions? }.
 */

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const SRC  = path.join(ROOT, 'src', 'tokens-studio.json');
const OUT  = path.join(ROOT, 'dist');

if (!fs.existsSync(SRC)) {
  console.error(`Missing source: ${SRC}`);
  console.error('Push your tokens from Tokens Studio for Figma first.');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

const data = JSON.parse(fs.readFileSync(SRC, 'utf8'));

// ----- helpers ----------------------------------------------------------

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

// Tokens Studio sometimes wraps tokens under a type-named group ("Color",
// "Dimension", "Number", "Opacity") at the top level of each set. Strip those.
const TYPE_WRAPPERS = new Set([
  'color', 'dimension', 'number', 'opacity', 'fontfamilies', 'fontweights',
  'shadow', 'gradient'
]);

// Walk the W3C tree, collecting [{ path: string[], type, value }] for each leaf.
function flatten(obj, prefix = []) {
  const out = [];
  if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
    if ('$value' in obj && '$type' in obj) {
      const clean = prefix.length && TYPE_WRAPPERS.has(prefix[0].toLowerCase())
        ? prefix.slice(1)
        : prefix;
      out.push({ path: clean, type: obj.$type, value: obj.$value });
    } else {
      for (const [key, val] of Object.entries(obj)) {
        if (key.startsWith('$')) continue;
        out.push(...flatten(val, [...prefix, key]));
      }
    }
  }
  return out;
}

// "Spiro Foo/Bar" → { category: "foo", mode: "Bar" }
function parseSetName(name) {
  const parts = name.split('/');
  const collection = parts[0].replace(/^Spiro\s+/i, '').trim().toLowerCase();
  const mode = parts[1] || 'Default';
  return { category: collection, mode };
}

// stroke/N (TS) → border/N (existing var name --spiro-border-1, etc.)
function renamePath(category, segments) {
  if (category === 'stroke' && segments[0] === 'stroke') {
    return ['border', ...segments.slice(1)];
  }
  return segments;
}

const cssName = (segments) => `--spiro-${segments.map(kebab).join('-')}`;

const normColor = (v) =>
  typeof v === 'string' && v.startsWith('#') ? v.toUpperCase() : v;

const normOpacity = (v) => {
  const n = parseFloat(v);
  if (Number.isNaN(n)) return v;
  return (n > 1 ? n / 100 : n).toFixed(2);
};

// ----- bucket tokens ----------------------------------------------------

const buckets = {
  color: { Light: [], Dark: [] },
  spacing: [],
  radius: [],
  stroke: [],
  opacity: [],
  typography: [],
  shadows: [],
  gradient: [],
};

// Convert a Tokens Studio boxShadow $value (object or array of objects) to a CSS box-shadow string.
function shadowToCss(value) {
  const layers = Array.isArray(value) ? value : [value];
  return layers.map(layer => {
    const inset = layer.type === 'innerShadow' ? 'inset ' : '';
    const x = layer.x ?? 0;
    const y = layer.y ?? 0;
    const blur = layer.blur ?? 0;
    const spread = layer.spread ?? 0;
    const color = layer.color ?? 'rgba(0,0,0,0.10)';
    return `${inset}${x}px ${y}px ${blur}px ${spread}px ${color}`;
  }).join(', ');
}
const unknown = [];

// Aliases — handle plural / variant set names that should map to canonical buckets.
const CATEGORY_ALIAS = {
  gradients: 'gradient',
  shadow: 'shadows',
};

for (const [setName, set] of Object.entries(data)) {
  const parsed = parseSetName(setName);
  const category = CATEGORY_ALIAS[parsed.category] || parsed.category;
  const mode = parsed.mode;
  const tokens = flatten(set);
  if (category === 'color') {
    buckets.color[mode] = (buckets.color[mode] || []).concat(tokens);
  } else if (buckets[category]) {
    buckets[category].push(...tokens);
  } else {
    unknown.push({ setName, count: tokens.length });
  }
}

if (unknown.length) {
  console.warn(`  Note: unhandled set(s):`, unknown.map((u) => `${u.setName} (${u.count})`).join(', '));
}

console.log(`  parsed:  color/Light=${buckets.color.Light.length}, color/Dark=${buckets.color.Dark.length}, spacing=${buckets.spacing.length}, radius=${buckets.radius.length}, stroke=${buckets.stroke.length}, opacity=${buckets.opacity.length}, typography=${buckets.typography.length}, shadows=${buckets.shadows.length}, gradient=${buckets.gradient.length}`);

// ----- step 1: tokens.css -----------------------------------------------

const lines = [];
lines.push('/*');
lines.push(' * Spiro Design Tokens');
lines.push(' * Auto-generated from packages/tokens/src/tokens-studio.json.');
lines.push(' * Do not edit by hand — edit in Tokens Studio for Figma instead.');
lines.push(' */');
lines.push('');
lines.push(':root {');

if (buckets.color.Light.length) {
  lines.push('  /* ---------- Color (light) ---------- */');
  for (const t of buckets.color.Light) lines.push(`  ${cssName(t.path)}: ${normColor(t.value)};`);
  lines.push('');
}
if (buckets.spacing.length) {
  lines.push('  /* ---------- Spacing ---------- */');
  for (const t of buckets.spacing) lines.push(`  ${cssName(t.path)}: ${t.value};`);
  lines.push('');
}
if (buckets.radius.length) {
  lines.push('  /* ---------- Radius ---------- */');
  for (const t of buckets.radius) {
    let v = t.value;
    if (t.path.some((s) => /pill/i.test(s))) v = '9999px';
    lines.push(`  ${cssName(t.path)}: ${v};`);
  }
  lines.push('');
}
if (buckets.stroke.length) {
  lines.push('  /* ---------- Stroke ---------- */');
  for (const t of buckets.stroke) lines.push(`  ${cssName(renamePath('stroke', t.path))}: ${t.value};`);
  lines.push('');
}
if (buckets.opacity.length) {
  lines.push('  /* ---------- Opacity ---------- */');
  for (const t of buckets.opacity) lines.push(`  ${cssName(t.path)}: ${normOpacity(t.value)};`);
  lines.push('');
}
if (buckets.gradient.length) {
  lines.push('  /* ---------- Gradient ---------- */');
  for (const t of buckets.gradient) {
    const name = t.path.map(kebab).join('-');
    lines.push(`  --spiro-gradient-${name}: ${t.value};`);
  }
  lines.push('');
}

lines.push('  /* ---------- Typography ---------- */');
// Line-height ratios live here, not in Tokens Studio. They're CSS-only
// because Figma's line-height field is per-text-style in pixels — not
// reconcilable with a single ratio scale. Designers in Figma use named
// text styles (display-72, body-16) which have the right line-height baked in.
const LINE_HEIGHTS = {
  tight:   '1.05',
  snug:    '1.2',
  normal:  '1.4',
  relaxed: '1.5',
  loose:   '1.65',
};
for (const [k, v] of Object.entries(LINE_HEIGHTS)) {
  lines.push(`  --spiro-line-height-${k}: ${v};`);
}
const TYPE_PREFIX = {
  fontFamily: 'font',
  fontSize: 'font-size',
  fontWeight: 'font-weight',
  letterSpacing: 'letter-spacing',
  paragraphSpacing: 'paragraph-spacing',
};
// CSS-side fallback stacks per primary font (added in CSS only — Figma uses just the primary).
const FONT_FALLBACKS = {
  display:     "'Inter', system-ui, sans-serif",
  sans:        "'Inter', system-ui, sans-serif",
  handwritten: 'cursive',
};
for (const t of buckets.typography) {
  const group = t.path[0];
  const prefix = TYPE_PREFIX[group];
  if (!prefix) continue;
  const name = t.path.slice(1).map(kebab).join('-');
  let value = t.value;
  if (group === 'fontFamily') {
    const primary = Array.isArray(value) ? value[0] : value;
    const quoted = /\s/.test(primary) ? `'${primary}'` : primary;
    const fallback = FONT_FALLBACKS[t.path[1]] || 'sans-serif';
    value = `${quoted}, ${fallback}`;
  } else if (group === 'letterSpacing' && typeof value === 'number') {
    // Figma stores as percent (-2) → CSS uses em (-0.02em).
    value = `${(value / 100).toFixed(3).replace(/0+$/, '').replace(/\.$/, '')}em`;
    if (value === 'em' || value === '0em') value = '0';
  }
  lines.push(`  --spiro-${prefix}-${name}: ${value};`);
}
lines.push('');

lines.push('  /* ---------- Motion ---------- */');
lines.push(`  --spiro-duration-fast: 120ms;`);
lines.push(`  --spiro-duration-base: 200ms;`);
lines.push(`  --spiro-duration-slow: 320ms;`);
lines.push(`  --spiro-easing-standard: cubic-bezier(0.2, 0, 0, 1);`);
lines.push(`  --spiro-easing-enter: cubic-bezier(0, 0, 0.2, 1);`);
lines.push(`  --spiro-easing-exit: cubic-bezier(0.4, 0, 1, 1);`);
lines.push('');

// Build a {name → cssString} map of shadows from the Tokens Studio Shadows/Default set.
const shadowsLight = {};
for (const t of buckets.shadows) {
  const name = t.path.map(kebab).join('-');
  shadowsLight[name] = shadowToCss(t.value);
}
// Fallback to hardcoded values if Tokens Studio set is empty (for safety).
if (Object.keys(shadowsLight).length === 0) {
  Object.assign(shadowsLight, {
    'xs':           '0 1px 2px 0 rgba(15,14,37,0.05)',
    'sm':           '0 1px 3px 0 rgba(15,14,37,0.10), 0 1px 2px -1px rgba(15,14,37,0.10)',
    'md':           '0 4px 6px -1px rgba(15,14,37,0.10), 0 2px 4px -2px rgba(15,14,37,0.08)',
    'lg':           '0 10px 15px -3px rgba(15,14,37,0.10), 0 4px 6px -4px rgba(15,14,37,0.08)',
    'xl':           '0 20px 25px -5px rgba(15,14,37,0.10), 0 8px 10px -6px rgba(15,14,37,0.05)',
    '2xl':          '0 25px 50px -12px rgba(15,14,37,0.25)',
    'inner':        'inset 0 2px 4px 0 rgba(15,14,37,0.05)',
    'focus':        '0 0 0 3px rgba(48,56,252,0.45)',
    'focus-danger': '0 0 0 3px rgba(239,68,68,0.45)',
  });
}
lines.push('  /* ---------- Shadow (light) ---------- */');
for (const [k, v] of Object.entries(shadowsLight)) lines.push(`  --spiro-shadow-${k}: ${v};`);
lines.push('}');
lines.push('');

if (buckets.color.Dark.length) {
  const lightMap = {};
  for (const t of buckets.color.Light) lightMap[cssName(t.path)] = normColor(t.value);

  lines.push(`[data-theme='dark'] {`);
  lines.push('  /* ---------- Color (dark) ---------- */');
  for (const t of buckets.color.Dark) {
    const name = cssName(t.path);
    const v = normColor(t.value);
    if (lightMap[name] !== v) lines.push(`  ${name}: ${v};`);
  }
  lines.push('');
  const shadowsDark = {
    'xs':           '0 1px 2px 0 rgba(0,0,0,0.40)',
    'sm':           '0 1px 3px 0 rgba(0,0,0,0.50), 0 1px 2px -1px rgba(0,0,0,0.40)',
    'md':           '0 4px 8px -1px rgba(0,0,0,0.55), 0 2px 4px -2px rgba(0,0,0,0.40)',
    'lg':           '0 10px 20px -3px rgba(0,0,0,0.60), 0 4px 8px -4px rgba(0,0,0,0.45)',
    'xl':           '0 20px 30px -5px rgba(0,0,0,0.65), 0 8px 12px -6px rgba(0,0,0,0.40)',
    '2xl':          '0 28px 56px -12px rgba(0,0,0,0.75)',
    'inner':        'inset 0 2px 4px 0 rgba(0,0,0,0.40)',
    'focus':        '0 0 0 3px rgba(141,152,253,0.55)',
    'focus-danger': '0 0 0 3px rgba(248,113,113,0.55)',
  };
  lines.push('  /* ---------- Shadow (dark) ---------- */');
  for (const [k, v] of Object.entries(shadowsDark)) lines.push(`  --spiro-shadow-${k}: ${v};`);
  lines.push('}');
}

fs.writeFileSync(path.join(OUT, 'tokens.css'), lines.join('\n') + '\n');
console.log('  wrote dist/tokens.css');

// ----- step 2: dist/tokens.json (W3C tree) ------------------------------

const w3c = { $description: 'Spiro Design Tokens (auto-generated)' };
const setLeaf = (root, segs, value, type) => {
  if (!segs.length) return;
  let node = root;
  for (let i = 0; i < segs.length - 1; i++) {
    if (!node[segs[i]] || node[segs[i]].$value !== undefined) node[segs[i]] = node[segs[i]] || {};
    node = node[segs[i]];
  }
  node[segs[segs.length - 1]] = { $value: value, $type: type };
};
w3c.color = {};
for (const t of buckets.color.Light) setLeaf(w3c.color, t.path, normColor(t.value), 'color');
w3c.spacing = {};
for (const t of buckets.spacing) {
  const segs = t.path[0] === 'space' ? t.path.slice(1) : t.path;
  setLeaf(w3c.spacing, segs, t.value, 'dimension');
}
w3c.radius = {};
for (const t of buckets.radius) {
  let v = t.value;
  if (t.path.some((s) => /pill/i.test(s))) v = '9999px';
  const segs = t.path[0] === 'radius' ? t.path.slice(1) : t.path;
  setLeaf(w3c.radius, segs, v, 'dimension');
}
w3c.border = {};
for (const t of buckets.stroke) {
  const segs = t.path[0] === 'stroke' ? t.path.slice(1) : t.path;
  setLeaf(w3c.border, segs, t.value, 'dimension');
}
w3c.opacity = {};
for (const t of buckets.opacity) {
  const segs = t.path[0] === 'opacity' ? t.path.slice(1) : t.path;
  setLeaf(w3c.opacity, segs, Number(normOpacity(t.value)), 'number');
}
w3c.shadow = {};
for (const [k, v] of Object.entries(shadowsLight)) w3c.shadow[k] = { $value: v, $type: 'shadow' };

fs.writeFileSync(path.join(OUT, 'tokens.json'), JSON.stringify(w3c, null, 2));
console.log('  wrote dist/tokens.json');

// ----- step 3: tokens.js / tokens.cjs / tokens.d.ts --------------------

const flat = {};
for (const t of buckets.color.Light) flat[camel(['color', ...t.path].join('-'))] = normColor(t.value);
for (const t of buckets.spacing)     flat[camel(t.path.join('-'))] = t.value;
for (const t of buckets.radius) {
  let v = t.value;
  if (t.path.some((s) => /pill/i.test(s))) v = '9999px';
  flat[camel(t.path.join('-'))] = v;
}
for (const t of buckets.stroke)  flat[camel(renamePath('stroke', t.path).join('-'))] = t.value;
for (const t of buckets.opacity) flat[camel(t.path.join('-'))] = normOpacity(t.value);
for (const [k, v] of Object.entries(shadowsLight)) flat[camel('shadow-' + k)] = v;

fs.writeFileSync(
  path.join(OUT, 'tokens.js'),
  `// Auto-generated. Do not edit.\nexport const tokens = ${JSON.stringify(flat, null, 2)};\nexport default tokens;\n`
);
fs.writeFileSync(
  path.join(OUT, 'tokens.cjs'),
  `// Auto-generated. Do not edit.\nmodule.exports = ${JSON.stringify(flat, null, 2)};\n`
);
fs.writeFileSync(
  path.join(OUT, 'tokens.d.ts'),
  [
    `// Auto-generated. Do not edit.`,
    `export interface SpiroTokens {`,
    ...Object.keys(flat).map((k) => `  ${JSON.stringify(k)}: string | number;`),
    `}`,
    `export declare const tokens: SpiroTokens;`,
    `export default tokens;`,
    ``,
  ].join('\n')
);
console.log('  wrote dist/tokens.{js,cjs,d.ts}');

// ----- step 4: tailwind preset -----------------------------------------

const colorTree = {};
for (const t of buckets.color.Light) {
  let node = colorTree;
  for (let i = 0; i < t.path.length - 1; i++) {
    if (typeof node[t.path[i]] === 'string') break;
    node[t.path[i]] = node[t.path[i]] || {};
    node = node[t.path[i]];
  }
  node[t.path[t.path.length - 1]] = `var(${cssName(t.path)})`;
}

const spacingScale = {};
for (const t of buckets.spacing) {
  const key = t.path[0] === 'space' ? t.path.slice(1).join('-') : t.path.join('-');
  spacingScale[key || t.path.join('-')] = t.value;
}
const radiusScale = {};
for (const t of buckets.radius) {
  const key = t.path[0] === 'radius' ? t.path.slice(1).join('-') : t.path.join('-');
  let v = t.value;
  if (t.path.some((s) => /pill/i.test(s))) v = '9999px';
  radiusScale[key || t.path.join('-')] = v;
}
const borderScale = {};
for (const t of buckets.stroke) {
  const segs = renamePath('stroke', t.path);
  const key = segs[0] === 'border' ? segs.slice(1).join('-') : segs.join('-');
  borderScale[key || segs.join('-')] = t.value;
}
const shadowScale = {};
for (const k of Object.keys(shadowsLight)) shadowScale[k] = `var(--spiro-shadow-${k})`;

const preset = `// Tailwind v3+ preset for the Spiro Design System.
// Auto-generated from tokens-studio.json. Do not edit.

module.exports = {
  theme: {
    extend: {
      colors: ${JSON.stringify(colorTree, null, 8)},
      backgroundImage: ${JSON.stringify(buckets.gradient.reduce((acc, t) => ({ ...acc, [t.path.map(kebab).join('-')]: `var(--spiro-gradient-${t.path.map(kebab).join('-')})` }), {}), null, 8)},
      spacing: ${JSON.stringify(spacingScale, null, 8)},
      borderRadius: ${JSON.stringify(radiusScale, null, 8)},
      borderWidth: ${JSON.stringify(borderScale, null, 8)},
      boxShadow: ${JSON.stringify(shadowScale, null, 8)},
      fontFamily: ${JSON.stringify(buckets.typography.filter(t => t.path[0] === 'fontFamily').reduce((acc, t) => {
        const primary = Array.isArray(t.value) ? t.value[0] : t.value;
        const fallback = FONT_FALLBACKS[t.path[1]] || 'sans-serif';
        const fallbackArr = fallback.split(',').map(s => s.trim().replace(/^['"]|['"]$/g, ''));
        return { ...acc, [t.path[1]]: [primary, ...fallbackArr] };
      }, {}), null, 8)},
      fontSize: ${JSON.stringify(buckets.typography.filter(t => t.path[0] === 'fontSize').reduce((acc, t) => ({ ...acc, [t.path[1]]: t.value }), {}), null, 8)},
      lineHeight: ${JSON.stringify(LINE_HEIGHTS, null, 8)},
      letterSpacing: ${JSON.stringify(buckets.typography.filter(t => t.path[0] === 'letterSpacing').reduce((acc, t) => {
        let v = typeof t.value === 'number' ? `${(t.value / 100).toFixed(3).replace(/0+$/, '').replace(/\.$/, '')}em` : t.value;
        if (v === 'em' || v === '0em') v = '0';
        return { ...acc, [t.path[1]]: v };
      }, {}), null, 8)},
      fontWeight: ${JSON.stringify(buckets.typography.filter(t => t.path[0] === 'fontWeight').reduce((acc, t) => ({ ...acc, [t.path[1]]: String(t.value) }), {}), null, 8)},
      transitionDuration: {
        fast: '120ms',
        DEFAULT: '200ms',
        slow: '320ms',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(0.2, 0, 0, 1)',
        enter: 'cubic-bezier(0, 0, 0.2, 1)',
        exit: 'cubic-bezier(0.4, 0, 1, 1)',
      },
    },
  },
};
`;
fs.writeFileSync(path.join(OUT, 'tailwind.preset.cjs'), preset);
console.log('  wrote dist/tailwind.preset.cjs');

console.log(`\n  Spiro tokens built →`, path.relative(process.cwd(), OUT));
