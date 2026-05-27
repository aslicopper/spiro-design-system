#!/usr/bin/env python3
"""
Build library/preview.html — the v0.16 single-file visual spec.

Design goals
------------
  • Minimal, design-system-first. No marketing copy, no imagery, no
    decorative gradients / image overlays.
  • Sticky top nav (logo + version + theme toggle).
  • Sticky left sidebar with jump-anchors to every section.
  • Click-to-copy on swatches, tokens, and code chips.
  • Typography laid out as a proper table (grouped by role family).
  • Brand-anchor colours (blue-500, volt-500) marked with a star.
  • Semantic tokens show the resolved colour next to the name.
  • Section headings use DM Sans (not Clash Grotesk) — Clash is reserved
    for display / amount roles.

Sections (sidebar order)
  Foundations  — Introduction
  Color        — Primitives · Backgrounds
  Type         — Typography
  Space        — Spacing · Radius · Borders · Shadows
  Components   — Buttons · Icons · Icon badges · Patterns
  Tokens       — Semantic tokens
"""
from pathlib import Path
from html import escape
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import FAMILIES, STEPS, BACKGROUND

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT    = PACKAGE_ROOT.parents[1]
TOKENS_PKG   = REPO_ROOT / "packages" / "tokens"
REACT_PKG    = REPO_ROOT / "packages" / "react"

OUT = PACKAGE_ROOT / "dist" / "index.html"
OUT.parent.mkdir(parents=True, exist_ok=True)

TOKENS_CSS = (TOKENS_PKG / "dist" / "tokens.css").read_text(encoding="utf-8")
FONTS_CSS  = (TOKENS_PKG / "dist" / "fonts.css").read_text(encoding="utf-8")
BTN_CSS    = (REACT_PKG / "src" / "Button" / "Button.css").read_text(encoding="utf-8")

import shutil
FONTS_SRC = TOKENS_PKG / "dist" / "fonts"
FONTS_DST = OUT.parent / "fonts"
if FONTS_SRC.exists():
    shutil.rmtree(FONTS_DST, ignore_errors=True)
    shutil.copytree(FONTS_SRC, FONTS_DST)

ICON_DIR    = PACKAGE_ROOT / "src" / "assets" / "icons" / "line"
BADGE_DIR   = PACKAGE_ROOT / "src" / "assets" / "icons" / "badges"
PATTERN_DIR = PACKAGE_ROOT / "src" / "assets" / "patterns"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def read_svg(p: Path) -> str:
    return p.read_text(encoding="utf-8")

# Brand anchors — these steps within their family get a star marker and
# the "primary" treatment throughout the palette.
BRAND_ANCHORS = {
    ("blue", "500"),
    ("volt", "500"),
}

def is_anchor(family, step):
    return (family, step) in BRAND_ANCHORS

# Contrast: WCAG relative luminance. Used to pick dark vs. light label text
# on each swatch — replaces `mix-blend-mode: difference`, which was creating
# unreadable labels on mid-chroma swatches (e.g. volt, rose).
def _luminance(hex_):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    def _ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * _ch(r) + 0.7152 * _ch(g) + 0.0722 * _ch(b)

def label_on(hex_):
    """Choose a readable label colour for text over the given hex swatch."""
    # Threshold tuned so brand yellows (volt, amber) take dark labels and
    # mid-dark blues/reds take light labels — works for the full palette.
    return "#0F0E25" if _luminance(hex_) > 0.48 else "#FBFAF7"

# Which primitives are referenced by semantic tokens?
# Built at import from SEMANTIC_TOKENS so the star/dot indicator stays in
# sync automatically when we add/remove semantic aliases.
SEMANTIC_USAGE = {}  # (family, step) -> [semantic token names]

def _build_usage():
    for group, name, var, light_ref, dark_ref, note in SEMANTIC_TOKENS:
        for ref in (light_ref, dark_ref):
            m = re.match(r"color\.(\w+)\.(\w+)", ref)
            if not m:
                continue
            key = (m.group(1), m.group(2))
            SEMANTIC_USAGE.setdefault(key, [])
            if name not in SEMANTIC_USAGE[key]:
                SEMANTIC_USAGE[key].append(name)

def usage_for(family, step):
    return SEMANTIC_USAGE.get((family, step), [])

# ------------------------------------------------------------------
# Color primitives — family × step table
# ------------------------------------------------------------------
def palette_row(name, colors, note):
    """One family row — 13 swatches + family name + note."""
    star = ' <span class="star" title="Brand anchor" aria-label="brand anchor">★</span>' if name in ("blue", "volt") else ''
    cells = []
    for step, hex_ in zip(STEPS, colors):
        token = f"color.{name}.{step}"
        label_color = label_on(hex_)
        marks = []
        if is_anchor(name, step):
            marks.append('<span class="mark mark--anchor" title="Brand anchor" aria-label="brand anchor">★</span>')
        usages = usage_for(name, step)
        if usages:
            title = "Used by: " + ", ".join(usages)
            marks.append(f'<span class="mark mark--used" title="{escape(title)}" aria-label="referenced by semantic tokens">●</span>')
        marks_html = "".join(marks)
        cells.append(
            f'<button class="swatch" style="background:{hex_}; color:{label_color};" '
            f'data-copy="{hex_}" title="Click to copy — {token}">'
            f'<span class="swatch__step">{step}{marks_html}</span>'
            f'<span class="swatch__hex">{hex_}</span>'
            f'</button>'
        )
    cells_html = "\n".join(cells)
    return (
        f'<div class="ramp">'
        f'<div class="ramp__meta">'
        f'<span class="ramp__name">{name}{star}</span>'
        f'<span class="ramp__note">{escape(note)}</span>'
        f'</div>'
        f'<div class="ramp__cells">{cells_html}</div>'
        f'</div>'
    )

# ------------------------------------------------------------------
# Background families
# ------------------------------------------------------------------
def bg_row(tint, steps):
    cells = []
    for step, hex_ in steps.items():
        token = f"bg.{tint}.{step}"
        label_color = label_on(hex_)
        cells.append(
            f'<button class="bg-swatch" style="background:{hex_}; color:{label_color};" '
            f'data-copy="{hex_}" title="Click to copy — {token}">'
            f'<span class="bg-swatch__step">{step}</span>'
            f'<code class="bg-swatch__hex">{hex_}</code>'
            f'</button>'
        )
    return (
        f'<div class="bg-row">'
        f'<h4 class="bg-row__name">{tint}</h4>'
        f'<div class="bg-row__cells">{"".join(cells)}</div>'
        f'</div>'
    )

# ------------------------------------------------------------------
# Typography — full 19-role table
# ------------------------------------------------------------------
# Neutral samples that exercise each role without marketing tone.
# Handwritten rows use the short phrase "Handwritten accent" — kept
# intentionally terse so Kalam's character shows without filler.
TYPE_ROLES = [
    # (group, token, sample, family, weight, size, lh, tracking)
    # Mirrors the Figma text-style import exactly — 28 numeric-named roles.
    ("Display",  "display-72", "Display 72",              "Clash Grotesk", "Semibold 600", "72", "1.05", "-2%"),
    ("Display",  "display-56", "Display 56",              "Clash Grotesk", "Semibold 600", "56", "1.08", "-2%"),
    ("Display",  "display-44", "Display 44",              "Clash Grotesk", "Semibold 600", "44", "1.10", "-2%"),
    ("Display",  "display-36", "Display 36",              "Clash Grotesk", "Semibold 600", "36", "1.15", "-2%"),
    ("Display",  "display-30", "Display 30",              "Clash Grotesk", "Semibold 600", "30", "1.20", "-2%"),

    ("Heading",  "heading-40", "Heading 40",              "DM Sans",       "SemiBold 600", "40", "1.15", "-2%"),
    ("Heading",  "heading-36", "Heading 36",              "DM Sans",       "SemiBold 600", "36", "1.20", "-2%"),
    ("Heading",  "heading-30", "Heading 30",              "DM Sans",       "SemiBold 600", "30", "1.25", "-2%"),
    ("Heading",  "heading-28", "Heading 28",              "DM Sans",       "SemiBold 600", "28", "1.27", "-2%"),
    ("Heading",  "heading-24", "Heading 24",              "DM Sans",       "SemiBold 600", "24", "1.30", "-2%"),
    ("Heading",  "heading-20", "Heading 20",              "DM Sans",       "SemiBold 600", "20", "1.35", "-2%"),
    ("Heading",  "heading-18", "Heading 18",              "DM Sans",       "SemiBold 600", "18", "1.40", "-2%"),
    ("Heading",  "heading-16", "Heading 16",              "DM Sans",       "SemiBold 600", "16", "1.40", "-2%"),

    ("Body",     "body-24",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "24", "1.50", "-2%"),
    ("Body",     "body-20",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "20", "1.50", "-2%"),
    ("Body",     "body-18",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "18", "1.55", "-2%"),
    ("Body",     "body-16",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "16", "1.50", "-2%"),
    ("Body",     "body-14",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "14", "1.50", "-2%"),
    ("Body",     "body-12",    "The quick brown fox jumps over the lazy dog.", "DM Sans", "Regular 400", "12", "1.50", "-2%"),

    # Label — DM Sans SemiBold, 0% letter-spacing, ALL CAPS
    ("Label",    "label-18",   "BUTTON LABEL",            "DM Sans",       "SemiBold 600", "18", "1.10", "0%"),
    ("Label",    "label-14",   "UPPERCASE LABEL",         "DM Sans",       "SemiBold 600", "14", "1.10", "0%"),
    ("Label",    "label-12",   "LABEL",                   "DM Sans",       "SemiBold 600", "12", "1.10", "0%"),

    # Button — DM Sans SemiBold
    ("Button",   "button-20",  "Click me",                "DM Sans",       "SemiBold 600", "20", "1.0", "-2%"),
    ("Button",   "button-18",  "Click me",                "DM Sans",       "SemiBold 600", "18", "1.0", "-2%"),
    ("Button",   "button-16",  "Click me",                "DM Sans",       "SemiBold 600", "16", "1.0", "-2%"),

    # Quote — Kalam (Regular for 24/36, Bold for 20)
    ("Quote",    "quote-36",   "Handwritten 36",          "Kalam",         "Regular 400",  "36", "1.30", "-2%"),
    ("Quote",    "quote-24",   "Handwritten 24",          "Kalam",         "Regular 400",  "24", "1.40", "-2%"),
    ("Quote",    "quote-20",   "Handwritten bold",        "Kalam",         "Bold 700",     "20", "1.40", "-2%"),
]

def type_table():
    rows_html = []
    last_group = None
    for group, token, sample, family, weight, size, lh, track in TYPE_ROLES:
        if group != last_group:
            rows_html.append(
                f'<tr class="t-table__group"><td colspan="7">{group}</td></tr>'
            )
            last_group = group
        role_mod = f"t-sample--{token}"
        rows_html.append(
            f'<tr class="t-table__row">'
            f'<td class="t-table__token"><button class="copy-chip" data-copy="{token}" title="Copy token">{token}</button></td>'
            f'<td class="t-table__sample"><span class="t-sample {role_mod}">{escape(sample)}</span></td>'
            f'<td class="t-table__meta">{family}</td>'
            f'<td class="t-table__meta">{weight}</td>'
            f'<td class="t-table__meta mono">{size}</td>'
            f'<td class="t-table__meta mono">{lh}</td>'
            f'<td class="t-table__meta mono">{track}</td>'
            f'</tr>'
        )
    return (
        '<table class="t-table">'
        '<thead><tr>'
        '<th>Token</th><th>Sample</th><th>Family</th><th>Weight</th>'
        '<th>Size</th><th>LH</th><th>Tracking</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table>'
    )

# ------------------------------------------------------------------
# Spacing, Radius, Border width, Shadow tables
# ------------------------------------------------------------------
SPACE_SCALE = [
    ("space.0",  "0",  "0px"),
    ("space.1",  "4",  "4px"),
    ("space.2",  "8",  "8px"),
    ("space.3",  "12", "12px"),
    ("space.4",  "16", "16px"),
    ("space.5",  "20", "20px"),
    ("space.6",  "24", "24px"),
    ("space.8",  "32", "32px"),
    ("space.10", "40", "40px"),
    ("space.12", "48", "48px"),
    ("space.16", "64", "64px"),
    ("space.20", "80", "80px"),
]

def space_table():
    cards = []
    for token, px, val in SPACE_SCALE:
        cards.append(
            f'<div class="scale-card">'
            f'  <div class="scale-card__preview"><span class="space-bar" style="width:{px}px"></span></div>'
            f'  <div class="scale-card__meta">'
            f'    <button class="copy-chip" data-copy="{token}" title="Copy token">{token}</button>'
            f'    <span class="scale-card__value mono">{val}</span>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="scale-grid">{"".join(cards)}</div>'

RADIUS_SCALE = [
    ("radius.0",    "0",     "0"),
    ("radius.2",    "2px",   "2"),
    ("radius.4",    "4px",   "4"),
    ("radius.8",    "8px",   "8"),
    ("radius.12",   "12px",  "12"),
    ("radius.16",   "16px",  "16"),
    ("radius.24",   "24px",  "24"),
    ("radius.32",   "32px",  "32"),
    ("radius.pill", "9999px", "9999"),
]

def radius_table():
    cards = []
    for token, label, px in RADIUS_SCALE:
        val = f"{px}px" if token != "radius.pill" else "9999px"
        if token == "radius.0":
            val = "0"
        cards.append(
            f'<div class="scale-card">'
            f'  <div class="scale-card__preview"><span class="radius-demo" style="border-radius:{val}"></span></div>'
            f'  <div class="scale-card__meta">'
            f'    <button class="copy-chip" data-copy="{token}" title="Copy token">{token}</button>'
            f'    <span class="scale-card__value mono">{val}</span>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="scale-grid">{"".join(cards)}</div>'

BORDER_SCALE = [
    ("border.0", "0",   "0"),
    ("border.1", "1px", "1"),
    ("border.2", "2px", "2"),
    ("border.3", "3px", "3"),
]

def border_table():
    cards = []
    for token, label, px in BORDER_SCALE:
        if px == "0":
            preview = '<span class="border-demo border-demo--zero">— no border —</span>'
        else:
            preview = f'<span class="border-demo" style="border-width:{label}"></span>'
        cards.append(
            f'<div class="scale-card">'
            f'  <div class="scale-card__preview">{preview}</div>'
            f'  <div class="scale-card__meta">'
            f'    <button class="copy-chip" data-copy="{token}" title="Copy token">{token}</button>'
            f'    <span class="scale-card__value mono">{label}</span>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="scale-grid">{"".join(cards)}</div>'

SHADOW_SCALE = [
    ("shadow.xs",          "--spiro-shadow-xs"),
    ("shadow.sm",          "--spiro-shadow-sm"),
    ("shadow.md",          "--spiro-shadow-md"),
    ("shadow.lg",          "--spiro-shadow-lg"),
    ("shadow.xl",          "--spiro-shadow-xl"),
    ("shadow.2xl",         "--spiro-shadow-2xl"),
    ("shadow.inner",       "--spiro-shadow-inner"),
    ("shadow.focus",       "--spiro-shadow-focus"),
    ("shadow.focus-danger","--spiro-shadow-focus-danger"),
]

def shadow_table():
    cards = []
    for token, var in SHADOW_SCALE:
        cards.append(
            f'<div class="scale-card scale-card--shadow">'
            f'  <div class="scale-card__preview"><span class="shadow-cell"><span class="shadow-demo" style="box-shadow: var({var})"></span></span></div>'
            f'  <div class="scale-card__meta">'
            f'    <button class="copy-chip" data-copy="{token}" title="Copy token">{token}</button>'
            f'    <span class="scale-card__value mono">var({var})</span>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="scale-grid scale-grid--shadow">{"".join(cards)}</div>'

# ------------------------------------------------------------------
# Icons & patterns
# ------------------------------------------------------------------
def icon_cell(name, svg):
    return (
        f'<figure class="icon-cell">'
        f'<div class="icon-cell__art">{svg}</div>'
        f'<figcaption><button class="copy-chip" data-copy="{name}" title="Copy icon name">{name}</button></figcaption>'
        f'</figure>'
    )

def badge_cell(name, svg):
    label = name.replace("-", " ")
    return (
        f'<figure class="badge-cell">'
        f'<div class="badge-cell__art">{svg}</div>'
        f'<figcaption><button class="copy-chip" data-copy="{name}" title="Copy badge name">{label}</button></figcaption>'
        f'</figure>'
    )

# Pattern cells get BOTH a light-mode and dark-mode colour so dark
# patterns don't vanish on navy canvas. The data-theme override swaps
# --p-color inline on the container.
PATTERN_CONFIG = [
    ("var(--spiro-color-blue-500)",   "var(--spiro-color-blue-300)"),
    ("var(--spiro-color-zinc-900)",  "var(--spiro-color-zinc-100)"),
    ("var(--spiro-color-blue-700)",   "var(--spiro-color-blue-300)"),
    ("var(--spiro-color-orange-500)", "var(--spiro-color-orange-400)"),
    ("var(--spiro-color-blue-900)",   "var(--spiro-color-blue-200)"),
    ("var(--spiro-color-zinc-900)",  "var(--spiro-bg-cream-25)"),
]

def pattern_cell(name, svg, light, dark):
    return (
        f'<figure class="pattern-cell" style="--p-light:{light}; --p-dark:{dark};">'
        f'<div class="pattern-cell__art">{svg}</div>'
        f'<figcaption><button class="copy-chip" data-copy="{name}" title="Copy pattern name">{name}</button></figcaption>'
        f'</figure>'
    )

# ------------------------------------------------------------------
# Semantic tokens table
# ------------------------------------------------------------------
SEMANTIC_TOKENS = [
    # (group, name, css-var, resolves-to (light), resolves-to (dark), note)
    ("Surface",    "bg.canvas",        "--spiro-bg-canvas",        "bg.cream.25",     "bg.navy.950",    "Default page background."),
    ("Surface",    "bg.default",       "--spiro-bg-default",       "color.zinc.900",  "bg.cream.25",    "Inverse-style surface, zinc-anchored. Theme-flips."),
    ("Surface",    "bg.subtle",        "--spiro-bg-subtle",        "bg.cream.50",     "bg.navy.900",    "Hover-state for neutral surfaces."),
    ("Surface",    "bg.muted",         "--spiro-bg-muted",         "bg.cream.100",    "bg.navy.900",    "Secondary surface / card body."),
    ("Surface",    "bg.inverse",       "--spiro-bg-inverse",       "bg.navy.950",     "bg.cream.25",    "Inverse surface, navy-anchored. Theme-flips."),
    ("Surface",    "bg.blend",         "--spiro-bg-blend",         "navy 6%",         "cream 6%",       "Translucent inverse — overlay layer for tinting."),
    ("Surface",    "bg.contrast",      "--spiro-bg-contrast",      "#FFFFFF",          "#000000",        "Theme-flipping pure (white ↔ black)."),
    ("Surface",    "bg.black / bg.white", "--spiro-bg-black",      "static",           "static",         "Static pure colours; never flip."),

    ("Text",       "fg.default",       "--spiro-fg-default",       "color.zinc.900", "color.zinc.50",  "Default body text."),
    ("Text",       "fg.muted",         "--spiro-fg-muted",         "color.zinc.500", "color.zinc.400", "Meta / captions / labels."),
    ("Text",       "fg.muted-blend",   "--spiro-fg-muted-blend",   "zinc.900 60%",   "zinc.50 60%",    "Alpha-blend muted — same hue as default."),
    ("Text",       "fg.subtle",        "--spiro-fg-subtle",        "color.zinc.500", "color.zinc.500", "Tertiary — disabled copy."),
    ("Text",       "fg.subtle-blend",  "--spiro-fg-subtle-blend",  "zinc.900 40%",   "zinc.50 40%",    "Alpha-blend subtle."),
    ("Text",       "fg.on-accent",     "--spiro-fg-on-accent",     "#FBFAF7",        "#FBFAF7",        "Text on accent / status fills."),
    ("Text",       "fg.inverse",       "--spiro-fg-inverse",       "color.zinc.50",  "color.zinc.900", "Inverts with theme."),
    ("Text",       "fg.contrast",      "--spiro-fg-contrast",      "#FFFFFF",        "#000000",        "Theme-flipping pure (white ↔ black)."),
    ("Text",       "fg.black / fg.white", "--spiro-fg-black",      "static",         "static",         "Static pure colours; never flip."),

    ("Border",     "border.subtle",    "--spiro-border-subtle",    "color.zinc.100", "color.zinc.800", "Default divider."),
    ("Border",     "border.default",   "--spiro-border-default",   "color.zinc.200", "color.zinc.700", "Input borders."),
    ("Border",     "border.strong",    "--spiro-border-strong",    "color.zinc.300", "color.zinc.500", "Hover / selected state."),
    ("Border",     "border.blend",     "--spiro-border-blend",     "zinc.500 20%",   "zinc.500 20%",   "Alpha-blend border — same hue as fg.subtle."),
    ("Border",     "border.focus",     "--spiro-border-focus",     "color.blue.500", "color.blue.400", "Focus ring."),

    ("Accent",     "accent.default",   "--spiro-accent-default",   "color.blue.500",   "color.blue.400", "Primary brand — Spiro Blue."),
    ("Accent",     "accent.hover",     "--spiro-accent-hover",     "color.blue.600",   "color.blue.300", "Hover state."),
    ("Accent",     "accent.pressed",   "--spiro-accent-pressed",   "color.blue.700",   "color.blue.500", "Pressed state (was 'active')."),
    ("Accent",     "accent.selected",  "--spiro-accent-selected",  "color.blue.500",   "color.blue.400", "Selected tab/segment background."),
    ("Accent",     "accent.deselected","--spiro-accent-deselected","color.blue.50",    "blue.700 40%",   "Unselected tab/segment background."),
    ("Accent",     "accent.subtle",    "--spiro-accent-subtle",    "color.blue.50",    "color.blue.800", "Subtle accent surface."),

    ("Status",     "danger.default",   "--spiro-danger-default",   "color.red.500",    "color.red.400",  "Destructive actions, errors."),
    ("Status",     "danger.hover",     "--spiro-danger-hover",     "color.red.600",    "color.red.300",  "Hover state."),
    ("Status",     "success.default",  "--spiro-success-default",  "color.emerald.500","color.emerald.400","Positive confirmation."),
    ("Status",     "warning.default",  "--spiro-warning-default",  "color.amber.500",  "color.amber.400","Warnings."),
    ("Status",     "info.default",     "--spiro-info-default",     "color.sky.500",    "color.sky.400",  "Informational."),

    ("Decorative", "decorative-fg/* (×13)", "--spiro-decorative-fg-...", "soft / bold / dark", "soft / bold / dark", "Chromatic accents (orange, amber, …, blue, red) for icons / illustrations."),
    ("Decorative", "decorative-bg/* (×19)", "--spiro-decorative-bg-...", "soft / bold / dark", "soft / bold / dark", "Tinted decorative surfaces. 13 chromatic + 4 pastel + cream + navy."),
]

def semantic_table():
    rows = []
    last_group = None
    for group, name, var, light_ref, dark_ref, note in SEMANTIC_TOKENS:
        if group != last_group:
            rows.append(f'<tr class="sem-table__group"><td colspan="5">{group}</td></tr>')
            last_group = group
        rows.append(
            f'<tr>'
            f'<td><button class="copy-chip" data-copy="{name}" title="Copy token">{name}</button></td>'
            f'<td><span class="sem-swatch" data-var="{var}" title="Resolved — light theme"></span>'
            f'<span class="mono tiny">{light_ref}</span></td>'
            f'<td><span class="sem-swatch sem-swatch--dark" data-var="{var}" data-theme-force="dark" title="Resolved — dark theme"></span>'
            f'<span class="mono tiny">{dark_ref}</span></td>'
            f'<td><code class="mono tiny">var({var})</code></td>'
            f'<td class="sem-table__note">{escape(note)}</td>'
            f'</tr>'
        )
    return (
        '<table class="sem-table">'
        '<thead><tr>'
        '<th>Token</th><th>Light</th><th>Dark</th><th>CSS var</th><th>Notes</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table>'
    )

# ------------------------------------------------------------------
# Decorative section — show every decorative-fg / decorative-bg token
# ------------------------------------------------------------------
DECORATIVE_FG_FAMILIES = ["blue","orange","amber","yellow","lime","emerald","cyan","sky","indigo","violet","pink","rose","red","cream","navy"]
DECORATIVE_BG_FAMILIES = ["blue","orange","amber","yellow","lime","emerald","cyan","sky","indigo","violet","pink","rose","red","lavender","mint","peach","periwinkle","cream","navy"]

def decorative_section():
    def family_row(family, kind):
        # Render 3 swatches (soft / bold / dark) using CSS vars so they flip with theme
        cells = []
        for tone in ("soft", "bold", "dark"):
            var = f"--spiro-decorative-{kind}-{family}-{tone}"
            token = f"decorative-{kind}/{family}-{tone}"
            cells.append(
                f'<button class="deco-cell" style="background: var({var});" '
                f'data-copy="{token}" title="Click to copy — {token}">'
                f'<span class="deco-cell__tone">{tone}</span>'
                f'</button>'
            )
        return (
            f'<div class="deco-row">'
            f'<span class="deco-row__name">{family}</span>'
            f'<div class="deco-row__cells">{"".join(cells)}</div>'
            f'</div>'
        )
    fg_rows = "".join(family_row(f, "fg") for f in DECORATIVE_FG_FAMILIES)
    bg_rows = "".join(family_row(f, "bg") for f in DECORATIVE_BG_FAMILIES)
    return (
        f'<h3 class="deco-h">decorative-fg <span class="deco-h__count">{len(DECORATIVE_FG_FAMILIES) * 3} tokens</span></h3>'
        f'<div class="deco-grid">{fg_rows}</div>'
        f'<h3 class="deco-h">decorative-bg <span class="deco-h__count">{len(DECORATIVE_BG_FAMILIES) * 3} tokens</span></h3>'
        f'<div class="deco-grid">{bg_rows}</div>'
    )

# ------------------------------------------------------------------
# Gradients section — render each as a real CSS gradient
# ------------------------------------------------------------------
# (name, css gradient value, optional note)
GRADIENT_LIST = [
    # Solid feature
    ("hero",                "linear-gradient(135deg, #1F27E5, #3038FC, #DFFF04)", "blue.600 → blue.500 → volt.500"),
    ("dawn",                "linear-gradient(180deg, #FBBF24, #EF4444)", "amber.400 → red.500"),
    ("brand",               "linear-gradient(180deg, #1F27E5, #151A8F)", "blue.600 → blue.800"),
    # Pastel fades
    ("lavender-soft-fade",  "linear-gradient(180deg, #F2F1F6FF, #F2F1F600)", ""),
    ("lavender-bold-fade",  "linear-gradient(180deg, #E5E3EBFF, #E5E3EB00)", ""),
    ("mint-soft-fade",      "linear-gradient(180deg, #E9F2ECFF, #E9F2EC00)", ""),
    ("mint-bold-fade",      "linear-gradient(180deg, #DCE8DFFF, #DCE8DF00)", ""),
    ("peach-soft-fade",     "linear-gradient(180deg, #F1ECE3FF, #F1ECE300)", ""),
    ("peach-bold-fade",     "linear-gradient(180deg, #E5D8C7FF, #E5D8C700)", ""),
    ("periwinkle-soft-fade","linear-gradient(180deg, #E8EDF3FF, #E8EDF300)", ""),
    ("periwinkle-bold-fade","linear-gradient(180deg, #DBE4EDFF, #DBE4ED00)", ""),
    # Brand
    ("blue-soft-fade",      "linear-gradient(180deg, #EEF0FFFF, #EEF0FF00)", ""),
    ("blue-bold-fade",      "linear-gradient(180deg, #DADCFFFF, #DADCFF00)", ""),
    ("volt-soft-fade",      "linear-gradient(180deg, #FBFFE5FF, #FBFFE500)", ""),
    # Neutrals
    ("cream-fade",          "linear-gradient(180deg, #F6F4EEFF, #F6F4EE00)", ""),
    ("zinc-soft-fade",      "linear-gradient(180deg, #F4F4F5FF, #F4F4F500)", ""),
    ("navy-fade",           "linear-gradient(180deg, #0F0E25FF, #0F0E2500)", ""),
    # Status
    ("success-fade",        "linear-gradient(180deg, #D1FAE5FF, #D1FAE500)", ""),
    ("warning-fade",        "linear-gradient(180deg, #FEF3C7FF, #FEF3C700)", ""),
    ("danger-fade",         "linear-gradient(180deg, #FEE2E2FF, #FEE2E200)", ""),
    ("info-fade",           "linear-gradient(180deg, #E0F2FEFF, #E0F2FE00)", ""),
    # Chromatic fades
    ("orange-soft-fade",    "linear-gradient(180deg, #FFF7EDFF, #FFF7ED00)", ""),
    ("orange-bold-fade",    "linear-gradient(180deg, #FFEDD5FF, #FFEDD500)", ""),
    ("amber-soft-fade",     "linear-gradient(180deg, #FFFBEBFF, #FFFBEB00)", ""),
    ("amber-bold-fade",     "linear-gradient(180deg, #FEF3C7FF, #FEF3C700)", ""),
    ("yellow-soft-fade",    "linear-gradient(180deg, #FEFCE8FF, #FEFCE800)", ""),
    ("yellow-bold-fade",    "linear-gradient(180deg, #FEF9C3FF, #FEF9C300)", ""),
    ("lime-soft-fade",      "linear-gradient(180deg, #F7FEE7FF, #F7FEE700)", ""),
    ("lime-bold-fade",      "linear-gradient(180deg, #ECFCCBFF, #ECFCCB00)", ""),
    ("emerald-soft-fade",   "linear-gradient(180deg, #ECFDF5FF, #ECFDF500)", ""),
    ("emerald-bold-fade",   "linear-gradient(180deg, #D1FAE5FF, #D1FAE500)", ""),
    ("cyan-soft-fade",      "linear-gradient(180deg, #ECFEFFFF, #ECFEFF00)", ""),
    ("cyan-bold-fade",      "linear-gradient(180deg, #CFFAFEFF, #CFFAFE00)", ""),
    ("sky-soft-fade",       "linear-gradient(180deg, #F0F9FFFF, #F0F9FF00)", ""),
    ("sky-bold-fade",       "linear-gradient(180deg, #E0F2FEFF, #E0F2FE00)", ""),
    ("indigo-soft-fade",    "linear-gradient(180deg, #EEF2FFFF, #EEF2FF00)", ""),
    ("indigo-bold-fade",    "linear-gradient(180deg, #E0E7FFFF, #E0E7FF00)", ""),
    ("violet-soft-fade",    "linear-gradient(180deg, #F5F3FFFF, #F5F3FF00)", ""),
    ("violet-bold-fade",    "linear-gradient(180deg, #EDE9FEFF, #EDE9FE00)", ""),
    ("pink-soft-fade",      "linear-gradient(180deg, #FDF2F8FF, #FDF2F800)", ""),
    ("pink-bold-fade",      "linear-gradient(180deg, #FCE7F3FF, #FCE7F300)", ""),
    ("rose-soft-fade",      "linear-gradient(180deg, #FFF1F2FF, #FFF1F200)", ""),
    ("rose-bold-fade",      "linear-gradient(180deg, #FFE4E6FF, #FFE4E600)", ""),
    ("red-soft-fade",       "linear-gradient(180deg, #FEF2F2FF, #FEF2F200)", ""),
    ("red-bold-fade",       "linear-gradient(180deg, #FEE2E2FF, #FEE2E200)", ""),
]

def gradients_section():
    cells = []
    for name, css, note in GRADIENT_LIST:
        token = f"gradient/{name}"
        # Layered: gradient on top of canvas so alpha-fades read correctly in both themes
        cells.append(
            f'<button class="grad-cell" data-copy="{token}" title="Click to copy — {token}">'
            f'<div class="grad-cell__art" style="background: {css};"></div>'
            f'<div class="grad-cell__meta"><span class="grad-cell__name">{name}</span>'
            + (f'<span class="grad-cell__note">{note}</span>' if note else '')
            + '</div></button>'
        )
    return f'<div class="grad-grid">{"".join(cells)}</div>'

# ------------------------------------------------------------------
# Component gallery — show all 14 components as static HTML mockups
# ------------------------------------------------------------------
def component_gallery():
    sections = []

    # Buttons (5 variants × 3 sizes = 15 quick examples)
    btn_rows = []
    for v, label in [('primary','Book ride'), ('secondary','Learn more'), ('ghost','View'), ('destructive','Cancel'), ('dark','Read'), ('light','Watch')]:
        cells = "".join(
            f'<button class="spiro-btn spiro-btn--{v} spiro-btn--{s}">{label}</button>'
            for s in ('sm','md','lg')
        )
        bg = "var(--spiro-bg-cream-25)" if v == 'dark' else ("var(--spiro-bg-navy-950)" if v == 'light' else "transparent")
        btn_rows.append(f'<div class="cg-row" style="background:{bg};">{cells}</div>')
    sections.append(f'<h3 class="cg-h">Button</h3><div class="cg-stack">{"".join(btn_rows)}</div>')

    # Chip
    chips = "".join([
        '<span class="cg-chip cg-chip--default">New</span>',
        '<span class="cg-chip cg-chip--selected">Active</span>',
        '<span class="cg-chip cg-chip--deselected">Pending</span>',
    ])
    sections.append(f'<h3 class="cg-h">Chip</h3><div class="cg-row">{chips}</div>')

    # Input
    inputs = """
        <div class="cg-input cg-input--default"><span>Enter your name</span></div>
        <div class="cg-input cg-input--focus"><span>Enter your name</span></div>
        <div class="cg-input cg-input--error"><span>Required field</span></div>
        <div class="cg-input cg-input--disabled"><span>Read-only</span></div>
    """
    sections.append(f'<h3 class="cg-h">Input</h3><div class="cg-stack">{inputs}</div>')

    # Badge
    badges = "".join([
        f'<span class="cg-badge" style="background: var(--spiro-{tone}-default); color: var(--spiro-fg-onAccent);">9</span>'
        for tone in ('accent','success','warning','danger','info')
    ])
    sections.append(f'<h3 class="cg-h">Badge</h3><div class="cg-row">{badges}</div>')

    # Switch (off / on)
    switches = """
        <div class="cg-switch cg-switch--off"><div class="cg-switch__thumb"></div></div>
        <div class="cg-switch cg-switch--on"><div class="cg-switch__thumb"></div></div>
    """
    sections.append(f'<h3 class="cg-h">Switch</h3><div class="cg-row">{switches}</div>')

    # Checkbox + Radio
    checks = """
        <div class="cg-check cg-check--unchecked"></div>
        <div class="cg-check cg-check--checked">✓</div>
        <div class="cg-check cg-check--indeterminate">—</div>
    """
    radios = """
        <div class="cg-radio cg-radio--off"></div>
        <div class="cg-radio cg-radio--on"></div>
    """
    sections.append(f'<h3 class="cg-h">Checkbox</h3><div class="cg-row">{checks}</div>')
    sections.append(f'<h3 class="cg-h">Radio</h3><div class="cg-row">{radios}</div>')

    # Tabs
    tabs = """
        <div class="cg-tab cg-tab--selected">Lease to own</div>
        <div class="cg-tab cg-tab--deselected">Pay upfront</div>
        <div class="cg-tab cg-tab--deselected">Fleet purchase</div>
    """
    sections.append(f'<h3 class="cg-h">Tabs / Segment</h3><div class="cg-row">{tabs}</div>')

    # Alert (4 tones)
    alerts = "".join([
        f'<div class="cg-alert cg-alert--{t}">'
        f'<div class="cg-alert__title">{title}</div>'
        f'<div class="cg-alert__body">{body}</div>'
        f'</div>'
        for t, title, body in [
            ('info', 'Heads up', 'Service centres open until 8 PM today.'),
            ('success', 'Saved', 'Your changes are live.'),
            ('warning', 'Service due', 'Book your 90-day check soon.'),
            ('danger', 'Action required', 'Payment failed — retry to continue.'),
        ]
    ])
    sections.append(f'<h3 class="cg-h">Alert</h3><div class="cg-stack">{alerts}</div>')

    # Modal
    modal = """
        <div class="cg-modal">
          <div class="cg-modal__head">
            <div class="cg-modal__title">Confirm action</div>
            <div class="cg-modal__close">×</div>
          </div>
          <div class="cg-modal__body">Are you sure you want to do this? This action cannot be undone.</div>
          <div class="cg-modal__actions">
            <button class="spiro-btn spiro-btn--secondary spiro-btn--md">Cancel</button>
            <button class="spiro-btn spiro-btn--primary spiro-btn--md">Confirm</button>
          </div>
        </div>
    """
    sections.append(f'<h3 class="cg-h">Modal</h3><div class="cg-stack">{modal}</div>')

    # Dropdown / Select
    dropdowns = """
        <div class="cg-dropdown cg-dropdown--default"><span>Select an option</span><span class="cg-dropdown__chev">▾</span></div>
        <div class="cg-dropdown cg-dropdown--focus"><span>Select an option</span><span class="cg-dropdown__chev">▾</span></div>
        <div class="cg-dropdown cg-dropdown--disabled"><span>Disabled</span><span class="cg-dropdown__chev">▾</span></div>
    """
    sections.append(f'<h3 class="cg-h">Dropdown</h3><div class="cg-stack">{dropdowns}</div>')

    # Tooltip
    tt = '<span class="cg-tooltip">Tooltip text here</span>'
    sections.append(f'<h3 class="cg-h">Tooltip</h3><div class="cg-row">{tt}</div>')

    # Accordion
    accordions = """
        <div class="cg-accordion cg-accordion--collapsed">
          <div class="cg-accordion__head"><span>How does battery swap work?</span><span class="cg-accordion__chev">▾</span></div>
        </div>
        <div class="cg-accordion cg-accordion--expanded">
          <div class="cg-accordion__head"><span>How does battery swap work?</span><span class="cg-accordion__chev">▴</span></div>
          <div class="cg-accordion__body">Roll into a swap station, slot in your spent battery, take a fresh one — under ninety seconds, no plug, no wait.</div>
        </div>
    """
    sections.append(f'<h3 class="cg-h">Accordion</h3><div class="cg-stack">{accordions}</div>')

    # Toast
    toasts = "".join([
        f'<div class="cg-toast cg-toast--{t}"><span class="cg-toast__icon">●</span><span>{msg}</span><span class="cg-toast__close">×</span></div>'
        for t, msg in [
            ('info', 'New service centre opening in Westlands'),
            ('success', 'Booking confirmed'),
            ('warning', 'Service due in 5 days'),
            ('danger', 'Payment failed — please retry'),
        ]
    ])
    sections.append(f'<h3 class="cg-h">Toast</h3><div class="cg-stack">{toasts}</div>')

    # Wrap each section (h3 + body) in a card and wrap the whole thing in
    # a masonry container. CSS columns handle the asymmetric layout.
    cards = "".join(f'<div class="cg-card">{sec}</div>' for sec in sections)
    return f'<div class="cg-masonry">{cards}</div>'

# ------------------------------------------------------------------
# Semantic tokens in context — a compact mock UI
# ------------------------------------------------------------------
# Every element inside .sem-preview reaches for a semantic token so that
# the same markup flips correctly between themes.
def semantic_preview():
    """Two-part preview:
       1. A realistic example card that exercises the most common tokens.
       2. A structured token strip showing every semantic token in its
          correct role (surface, text, border, accent, status) so the
          viewer can see each token's resolved colour in situ.
    """
    card = (
        '<div class="sem-preview__card">'
          '<div class="sem-preview__card-head">'
            '<div class="sem-preview__eyebrow" data-tk="fg.muted">Account</div>'
            '<div class="sem-preview__title" data-tk="fg.default">John Mwangi</div>'
            '<div class="sem-preview__sub"   data-tk="fg.muted-blend">Nairobi · Boda rider since 2024</div>'
          '</div>'
          '<div class="sem-preview__divider" data-tk="border.blend"></div>'
          # Tabs/Segment using accent.selected / accent.deselected — exercises the new state tokens
          '<div class="sem-preview__tabs">'
            '<span class="sem-preview__tab sem-preview__tab--selected"   data-tk="accent.selected / accent.selected-fg">Lease to own</span>'
            '<span class="sem-preview__tab sem-preview__tab--deselected" data-tk="accent.deselected / accent.deselected-fg">Pay upfront</span>'
            '<span class="sem-preview__tab sem-preview__tab--deselected" data-tk="accent.deselected / accent.deselected-fg">Fleet purchase</span>'
          '</div>'
          '<p class="sem-preview__p" data-tk="fg.default">Your bike is due for its 90-day service. Book a slot at your nearest service centre to keep your warranty active.</p>'
          '<p class="sem-preview__p sem-preview__p--muted" data-tk="fg.subtle-blend">Service takes roughly 45 minutes.</p>'
          '<div class="sem-preview__pill-row">'
            '<span class="sem-preview__pill sem-preview__pill--success" data-tk="success.default / fg.on-accent">Active</span>'
            '<span class="sem-preview__pill sem-preview__pill--warning" data-tk="warning.default / fg.on-accent">Service due</span>'
            '<span class="sem-preview__pill sem-preview__pill--info"    data-tk="info.default / fg.on-accent">Tip</span>'
            '<span class="sem-preview__pill sem-preview__pill--danger"  data-tk="danger.default / fg.on-accent">Overdue</span>'
          '</div>'
          # Decorative-bg sample — show how a tinted callout reads
          '<div class="sem-preview__deco" data-tk="decorative-bg/lavender-soft / decorative-fg/violet-bold">'
            '<span class="sem-preview__deco-dot" style="background: var(--spiro-decorative-fg-violet-bold);"></span>'
            '<span><strong>Tip:</strong> Decorative tokens drive editorial accents. This callout uses lavender-soft over violet-bold text.</span>'
          '</div>'
          '<div class="sem-preview__input" data-tk="bg.canvas / border.default / fg.default">'
            '<span class="sem-preview__input-label">Phone number</span>'
            '<span class="sem-preview__input-value">+254 712 345 678</span>'
          '</div>'
          '<div class="sem-preview__actions">'
            '<button class="sem-preview__btn sem-preview__btn--primary" data-tk="accent.default / fg.on-accent">Book service</button>'
            '<button class="sem-preview__btn sem-preview__btn--ghost"   data-tk="fg.default / border.default">View bike</button>'
            '<button class="sem-preview__btn sem-preview__btn--danger"  data-tk="danger.default / fg.on-accent">Cancel</button>'
          '</div>'
        '</div>'
    )
    note = (
        '<aside class="sem-preview__note">'
          '<h4>How to read this</h4>'
          '<p>The card above is built purely from semantic tokens — every colour, '
          'border, and surface. Hover any element to see which token(s) it pulls '
          'from. Below, each semantic token gets its own tile with a label. '
          'Toggle the theme (top-right) to see both flip.</p>'
        '</aside>'
    )

    # Full semantic-token strip — one tile per token, grouped.
    def tile(token, body_html, tk_ref=None):
        ref = tk_ref or token
        return (
            f'<div class="tk-tile" data-tk="{ref}" title="{escape(ref)}">'
            f'{body_html}'
            f'<span class="tk-tile__label">{token}</span>'
            f'</div>'
        )

    # Surface tiles — show the surface colour as the tile's own bg, with a
    # tiny sample of canvas/text contrast inside.
    surface = "".join([
        '<div class="tk-strip__group-title">Surface</div>',
        '<div class="tk-strip__grid">',
            tile("bg.canvas",  '<div class="tk-surface" style="background:var(--spiro-bg-canvas);color:var(--spiro-fg-default);border:1px solid var(--spiro-border-subtle);">Aa</div>'),
            tile("bg.subtle",  '<div class="tk-surface" style="background:var(--spiro-bg-subtle);color:var(--spiro-fg-default);border:1px solid var(--spiro-border-subtle);">Aa</div>'),
            tile("bg.muted",   '<div class="tk-surface" style="background:var(--spiro-bg-muted);color:var(--spiro-fg-default);border:1px solid var(--spiro-border-subtle);">Aa</div>'),
            tile("bg.inverse", '<div class="tk-surface" style="background:var(--spiro-bg-inverse);color:var(--spiro-fg-inverse);">Aa</div>'),
        '</div>',
    ])

    # Text tiles — each shows its colour as text against canvas or inverse.
    text = "".join([
        '<div class="tk-strip__group-title">Text</div>',
        '<div class="tk-strip__grid">',
            tile("fg.default",    '<div class="tk-text" style="color:var(--spiro-fg-default);">The quick brown fox</div>'),
            tile("fg.muted",      '<div class="tk-text" style="color:var(--spiro-fg-muted);">The quick brown fox</div>'),
            tile("fg.subtle",     '<div class="tk-text" style="color:var(--spiro-fg-subtle);">The quick brown fox</div>'),
            tile("fg.on-accent",  '<div class="tk-text tk-text--on-accent" style="background:var(--spiro-accent-default);color:var(--spiro-fg-on-accent);">On accent</div>'),
            tile("fg.inverse",    '<div class="tk-text tk-text--on-inverse" style="background:var(--spiro-bg-inverse);color:var(--spiro-fg-inverse);">Inverse text</div>'),
        '</div>',
    ])

    # Border tiles — each shows its border against canvas.
    borders = "".join([
        '<div class="tk-strip__group-title">Border</div>',
        '<div class="tk-strip__grid">',
            tile("border.subtle",  '<div class="tk-border" style="border-color:var(--spiro-border-subtle);"></div>'),
            tile("border.default", '<div class="tk-border" style="border-color:var(--spiro-border-default);"></div>'),
            tile("border.strong",  '<div class="tk-border" style="border-color:var(--spiro-border-strong);"></div>'),
        '</div>',
    ])

    # Accent — all three states
    accent = "".join([
        '<div class="tk-strip__group-title">Accent</div>',
        '<div class="tk-strip__grid">',
            tile("accent.default", '<div class="tk-fill" style="background:var(--spiro-accent-default);color:var(--spiro-fg-on-accent);">Default</div>'),
            tile("accent.hover",   '<div class="tk-fill" style="background:var(--spiro-accent-hover);color:var(--spiro-fg-on-accent);">Hover</div>'),
            tile("accent.active",  '<div class="tk-fill" style="background:var(--spiro-accent-active);color:var(--spiro-fg-on-accent);">Active</div>'),
            tile("accent.subtle",  '<div class="tk-fill tk-fill--soft" style="background:var(--spiro-accent-subtle);color:var(--spiro-accent-default);">Subtle</div>'),
        '</div>',
    ])

    # Status — 4 families, each with default + soft (bg+fg) where available
    status = "".join([
        '<div class="tk-strip__group-title">Status</div>',
        '<div class="tk-strip__grid">',
            tile("success.default", '<div class="tk-fill" style="background:var(--spiro-success-default);color:var(--spiro-fg-on-accent);">Success</div>'),
            tile("success.bg / success.fg",
                 '<div class="tk-fill tk-fill--soft" style="background:var(--spiro-success-bg);color:var(--spiro-success-fg);">Soft</div>',
                 tk_ref="success.bg / success.fg"),
            tile("warning.default", '<div class="tk-fill" style="background:var(--spiro-warning-default);color:var(--spiro-fg-on-accent);">Warning</div>'),
            tile("warning.bg / warning.fg",
                 '<div class="tk-fill tk-fill--soft" style="background:var(--spiro-warning-bg);color:var(--spiro-warning-fg);">Soft</div>',
                 tk_ref="warning.bg / warning.fg"),
            tile("danger.default",  '<div class="tk-fill" style="background:var(--spiro-danger-default);color:var(--spiro-fg-on-accent);">Danger</div>'),
            tile("danger.hover",    '<div class="tk-fill" style="background:var(--spiro-danger-hover);color:var(--spiro-fg-on-accent);">Hover</div>'),
            tile("danger.bg / danger.fg",
                 '<div class="tk-fill tk-fill--soft" style="background:var(--spiro-danger-bg);color:var(--spiro-danger-fg);">Soft</div>',
                 tk_ref="danger.bg / danger.fg"),
            tile("info.default",    '<div class="tk-fill" style="background:var(--spiro-info-default);color:var(--spiro-fg-on-accent);">Info</div>'),
            tile("info.bg / info.fg",
                 '<div class="tk-fill tk-fill--soft" style="background:var(--spiro-info-bg);color:var(--spiro-info-fg);">Soft</div>',
                 tk_ref="info.bg / info.fg"),
        '</div>',
    ])

    strip = (
        '<div class="tk-strip">'
          '<div class="tk-strip__head">Full semantic strip</div>'
          f'{surface}{text}{borders}{accent}{status}'
        '</div>'
    )

    return (
        '<div class="sem-preview">'
          f'{card}'
          f'{note}'
        '</div>'
        f'{strip}'
    )

# ------------------------------------------------------------------
# Prompts section — scaffolded, empty by default
# ------------------------------------------------------------------
# To add prompts later, append dicts of the form:
#   {"title": "...", "tags": ["..."], "description": "...", "body": "..."}
# to PROMPTS and re-run this script.
PROMPTS = [
    {
        "title": "3D product icon",
        "tags": ["3d", "image", "icon"],
        "description": "Generate on-brand clay-style isometric 3D icons for value-prop moments, empty states, and editorial callouts. Replace {{subject}} with a noun phrase like 'a battery' or 'a charging station'.",
        "body": """You are designing a single 3D product icon for the Spiro brand — a pan-African electric motorcycle and battery-swap company. Render a clay-like, matte-finish isometric icon of: {{subject}}.
Visual language
  • Style: soft-body 3D, inflated/clay aesthetic, chunky rounded geometry, no sharp edges
  • Camera: 3/4 top-down isometric (~30° elevation), orthographic-feel
  • Lighting: soft three-point — cool key from upper-left, warm fill, subtle rim
  • Finish: matte with gentle micro-roughness, no metallic specular, no plastic gloss
  • Shadow: short, soft contact shadow directly beneath, low opacity
  • Background: fully transparent PNG (no ground plane, no gradient, no vignette)
Palette (Spiro v0.4) — use sparingly, one or two accents max
  • Primary accent:  #3038FC (Spiro Blue 500)
  • Secondary:       #DFFF04 (Spiro Volt 500) — reserved for a single highlight like a cable tip, battery band, or glow dot; never a full surface
  • Neutral body:    #F1ECE3 (Cream) or #1A1833 (Navy) for base mass
  • Accent warm:     #F97316 (Orange 500) for service / utility subjects only
  • Accent cool:     #34D399 (Emerald 400) for safety / sustainability subjects only
Composition
  • Centred in frame, 15% padding on all sides
  • Silhouette must read clearly at 48px (squint test)
  • One dominant volume + at most two secondary elements
  • Avoid text, numbers, logos, or country-specific cues
Output
  • Square aspect ratio (1:1)
  • 1024×1024 minimum
  • Transparent PNG
  • No watermarks
Reference mood: Spline / Blender matte clay icons, the Apple Arcade style, the Behance "isometric 3D icon" trend — but softer, more Afro-futurist.
Negative prompt
  no photoreal, no glass, no metal, no glossy plastic, no harsh reflections, no gradient background, no drop shadow fade, no text, no watermark, no humans, no faces, no logos, no brand marks.""",
    },
    {
        "title": "Nairobi street stage — wide cinematic backdrop",
        "tags": ["photo", "21:9", "scene"],
        "description": "Ultra-wide 21:9 photographic backdrop with a clean centre stage for compositing in a motorcycle. Modern Westlands / Upper Hill / Kilimani vibe, low-angle camera, decorative African geometric motifs framing the scene.",
        "body": """Ultra-wide cinematic 21:9 ratio photograph. A wide, open street-level scene in an upscale modern Nairobi urban neighborhood — think Westlands, Upper Hill, or Kilimani — shot in bright clean daylight. The camera is positioned low — approximately 50cm above the ground, lens parallel to the pavement — creating a dramatic low-angle perspective. Slight upward tilt so the sky occupies the upper 40% of the frame.
On the far left edge of the frame, a low white plastered boundary wall is partially visible — occupying roughly 5% of the frame width. The wall is approximately 1.2 meters tall, painted in clean pure soft white with a smooth modern plaster finish. A single horizontal decorative band runs across it at mid-height — a concentric rotated diamond geometric pattern in muted terracotta red, faded indigo blue, and thin ochre gold lines, inspired by East African mural traditions. Above and below the band, the wall is plain smooth white plaster. On the far right edge of the frame, a matching low white boundary wall mirrors the left — same height, same decorative band, also occupying roughly 5% of the frame width. The two walls are far apart, framing the wide open center.
The center 90% of the frame is completely open and spacious. The ground is smooth, clean polished concrete or high-quality light gray paving tiles — like a modern commercial plaza or upscale pedestrian boulevard. The surface is clean, well-maintained, and urban — no dust, no sand, no dirt, no unpaved areas visible anywhere. Visible hairline joints between tiles and subtle tonal variation so it reads as real material. Gentle shadows from the walls fall onto the ground from clear overhead sun, adding depth. The very center of the ground plane is deliberately empty and unobstructed — a clean product stage for an electric motorcycle to be composited in later.
Beyond the courtyard, a modern paved Nairobi road is visible in the middle distance — smooth dark asphalt with clear white lane markings, well-maintained, urban. On the road, two or three vehicles are captured in motion with natural motion blur — a modern matatu minibus and a sedan moving left to right. A single boda-boda motorcycle passes in the far lane, also motion-blurred. On the far sidewalk beyond the road — which is a proper paved sidewalk, not a dirt shoulder — one or two pedestrians walk mid-stride, slightly motion-blurred, dressed in contemporary East African everyday clothing. All moving elements are background only, behind the courtyard stage.
Beyond the road, the Nairobi city skyline is visible — modern glass towers, the KICC tower silhouette, construction cranes — clear and sharp against the sky with clean atmospheric perspective. No dust haze, no orange smoke, no pollution — the air is clear and fresh. Between the road and skyline, a few well-maintained tropical trees — a palm tree and a flame tree with vivid orange-red blossoms — break the skyline naturally. The vegetation is lush and green, not dry or dusty.
The sky above is bright saturated blue with soft white cumulus clouds, sunlit and expansive — clean open space ideal for text overlay.
Lighting is bright, clean, natural midday daylight. No golden hour, no yellow cast, no warm dust haze. The atmosphere is clear and crisp. Shadows are defined with neutral tone. The white walls read as pure clean white. The overall image feels modern, premium, and distinctly urban Nairobi — not rural, not dusty, not village-like. A very subtle lens vignette gently darkens the far corners, drawing the eye to center stage.
No text, no logos. The center foreground is completely empty and unobstructed. Photorealistic, editorial quality, high production value. Wide-angle lens, low camera height at 50cm, centered symmetrical composition. Color grade is natural, balanced, and bright with neutral white balance — clean air, no dust particles, no haze, no orange atmospheric tint.""",
    },
    {
        "title": "Circular roofless studio — premium product stage",
        "tags": ["photo", "21:9", "studio", "product"],
        "description": "Minimalist circular roofless studio environment for premium automotive product photography. Empty centre stage, mashrabiya-inspired perforated frieze, soft pastel sky.",
        "body": """A minimalist circular roofless studio environment designed for
premium automotive product photography. Eye-level camera at
approximately 1.2 meters height, positioned directly in front
of the center stage, looking straight across at the opposite
wall — a perfectly symmetrical head-on composition. The center
of the space is wide open and empty.
The architecture is a perfect circular amphitheater: one single
continuous curved wall wrapping 360 degrees around an expansive
empty central stage. The wall is approximately 1.8 meters tall,
pure soft matte white (RAL 9003), completely smooth, no texture,
no seams, no reflections.
Near the top of the wall, a horizontal perforated frieze band,
approximately 30cm tall, runs continuously around the full
circumference. The band sits with a clean solid white margin of
roughly 15cm above it and a similar margin below it, so the
cutout band is clearly framed by solid wall on both sides.
The frieze is an openwork screen cut clean through the wall: a
repeating African geometric pattern of concentric rotated
diamonds, with the diamond shapes as true negative space —
actual voids cut through a 6cm thick wall. Through these
cutouts, the real sky is visible as a direct continuation of
the sky above the wall. CRITICAL: the color, brightness, and
tone visible through the cutouts must be IDENTICAL to the sky
directly above the wall — same light pastel blue, same softness,
same atmospheric quality, NOT a darker or more saturated blue.
The cutouts should read as seamless windows to the same sky,
with the sky color flowing continuously from above the wall
into and through the perforations. No flat tile effect, no
saturated color blocks, no painted appearance inside the
cutouts.
Above the wall: a soft light pastel blue sky, gentle and
airy — the color of a clear morning sky, not a deep saturated
afternoon sky. Think pale cerulean fading to near-white near
the horizon. A few small, soft, scattered white cumulus
clouds drift across the upper portion of the sky — lightweight,
wispy, unhurried, adding depth and realism without dominating
the composition. Clouds should be widely spaced, not clustered,
and soft-edged.
The floor is a large circular disc of polished off-white concrete,
matte with the faintest sheen, perfectly clean, with a subtle
radial gradient where light pools gently toward the center.
Soft diamond-shaped light patches cast from the frieze cutouts
fall naturally across the floor near the wall base on the
sunlit side.
Lighting: clean bright overhead midday daylight, slightly soft
and diffuse (as if very high thin cloud cover is softening
direct sun). Strictly cool-neutral white — no warm tones, no
golden hour, no amber. Even wash across the space.
The central stage is completely empty — reserved for product
placement.
Aesthetic: cinematic architectural product photography, Apple
keynote stage, Zaha Hadid minimalism, mashrabiya-inspired
contemporary architecture, bright airy premium studio. Shot on
medium format, f/8, ultra-sharp, no motion blur, no lens flare.
Aspect ratio: 21:9 cinematic.""",
    },
]

def prompts_section():
    if not PROMPTS:
        return (
            '<div class="prompt-empty">'
            '<div class="prompt-empty__art" aria-hidden="true">✎</div>'
            '<div class="prompt-empty__title">No prompts yet</div>'
            '<p class="prompt-empty__body">'
            'This is where reusable prompts will live. Each prompt gets its own card '
            'with a title, tags, description, and a copyable body. '
            'Add entries to the <code>PROMPTS</code> list in <code>build_preview.py</code>.'
            '</p>'
            '</div>'
        )
    cards = []
    for p in PROMPTS:
        tags_html = "".join(f'<span class="prompt-card__tag">{escape(t)}</span>' for t in p.get("tags", []))
        cards.append(
            f'<article class="prompt-card">'
            f'<header class="prompt-card__head">'
            f'<h3 class="prompt-card__title">{escape(p["title"])}</h3>'
            f'<div class="prompt-card__tags">{tags_html}</div>'
            f'</header>'
            f'<p class="prompt-card__desc">{escape(p.get("description",""))}</p>'
            f'<div class="prompt-card__body">'
            f'<button class="spiro-btn spiro-btn--secondary spiro-btn--sm prompt-card__copy" data-copy="{escape(p["body"])}">Copy prompt</button>'
            f'<pre>{escape(p["body"])}</pre>'
            f'</div>'
            f'</article>'
        )
    return f'<div class="prompt-stack">{"".join(cards)}</div>'

# ------------------------------------------------------------------
# Button demo — clean, no marketing copy
# ------------------------------------------------------------------
# Labels intentionally generic DS copy, not CTAs.
BTN_VARIANTS = [
    ("primary",     "Primary",     "Brand-blue CTA",                 "standard"),
    ("secondary",   "Secondary",   "Neutral bordered",               "standard"),
    ("ghost",       "Ghost",       "Transparent / inline",           "standard"),
    ("destructive", "Destructive", "Irreversible actions",           "standard"),
    ("dark",        "Dark",        "Navy-filled — for cream / tinted sections", "cream"),
    ("light",       "Light",       "Cream-filled — for navy / hero sections",  "dark"),
]

def button_rows():
    rows = []
    for variant, label, desc, bg in BTN_VARIANTS:
        row_cls = f"btn-row btn-row--{bg}"
        rows.append(
            f'<div class="{row_cls}">'
            f'<div class="btn-row__meta">'
            f'<code class="btn-row__name">{variant}</code>'
            f'<span class="btn-row__desc">{desc}</span>'
            f'</div>'
            f'<div class="btn-row__cells">'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--sm">{label}</button>'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--md">{label}</button>'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--lg">{label}</button>'
            f'</div>'
            f'<div class="btn-row__states">'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--md" disabled>Disabled</button>'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--md" aria-busy="true">'
            f'<span class="spiro-btn__spinner" aria-hidden="true"></span>'
            f'<span class="spiro-btn__label">Loading</span></button>'
            f'<button class="spiro-btn spiro-btn--{variant} spiro-btn--md" data-success-demo>'
            f'<span class="spiro-btn__label">Click for success</span></button>'
            f'</div>'
            f'</div>'
        )
    return "\n".join(rows)

# ------------------------------------------------------------------
# App CSS
# ------------------------------------------------------------------
APP_CSS = r"""
/* ===== Reset / base ===== */
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--spiro-font-sans);
  font-size: var(--spiro-font-size-base);
  line-height: 1.5;
  color: var(--spiro-fg-default);
  background: var(--spiro-bg-canvas);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  letter-spacing: var(--spiro-letter-tight);
}
button { font: inherit; }
code, .mono { font-family: var(--spiro-font-mono, ui-monospace, SFMono-Regular, Menlo, monospace); }
.tiny { font-size: 11px; }

/* Headings use DM Sans SemiBold (the heading scale), not Clash Grotesk.
   Clash is reserved for display + amount roles. */
h1, h2, h3, h4, h5 {
  font-family: var(--spiro-font-sans);
  font-weight: 600;
  letter-spacing: var(--spiro-letter-tight);
  margin: 0;
  color: var(--spiro-fg-default);
}
h2 { font-size: 30px; line-height: 1.25; margin: 0 0 8px 0; }
h3 { font-size: 20px; line-height: 1.35; margin: 0 0 6px 0; }
h4 { font-size: 14px; line-height: 1.3; text-transform: uppercase; letter-spacing: 0.08em;
     color: var(--spiro-fg-muted); font-weight: 600; margin: 0 0 12px 0; }
p  { margin: 0 0 12px 0; color: var(--spiro-fg-default); }

.eyebrow {
  color: var(--spiro-fg-muted);
  font-size: 13px;
  max-width: 64ch;
  margin: 0 0 24px 0;
}

/* ===== Top nav ===== */
.nav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 56px;
  padding: 0 20px;
  background: var(--spiro-bg-canvas);
  border-bottom: 1px solid var(--spiro-border-subtle);
}
.nav__brand {
  display: inline-flex; align-items: center; gap: 8px;
  font-weight: 600; font-size: 14px; color: var(--spiro-fg-default);
  text-decoration: none;
}
.nav__logo {
  width: 18px; height: 18px;
  border-radius: var(--spiro-radius-pill);
  background: var(--spiro-accent-default);
  display: inline-block;
}
.nav__version {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--spiro-radius-pill);
  background: var(--spiro-bg-subtle);
  color: var(--spiro-fg-muted);
  letter-spacing: 0.02em;
}
.nav__spacer { flex: 1; }
.nav__action {
  appearance: none; border: 1px solid var(--spiro-border-default);
  background: var(--spiro-bg-canvas);
  color: var(--spiro-fg-default);
  font-size: 13px;
  padding: 6px 12px;
  border-radius: var(--spiro-radius-pill);
  cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
}
.nav__action:hover { background: var(--spiro-bg-subtle); }

/* ===== Layout grid ===== */
.app {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 0;
  min-height: calc(100vh - 56px);
}

/* ===== Sidebar ===== */
.sidebar {
  position: sticky;
  top: 56px;
  align-self: start;
  height: calc(100vh - 56px);
  overflow-y: auto;
  padding: 24px 0 32px 20px;
  border-right: 1px solid var(--spiro-border-subtle);
  background: var(--spiro-bg-canvas);
}
.sidebar__group { margin-bottom: 20px; }
.sidebar__group h4 {
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--spiro-fg-muted);
  margin: 0 0 6px 0;
  padding: 0 8px;
  font-weight: 600;
}
.sidebar a {
  display: block;
  padding: 4px 10px;
  font-size: 13px;
  color: var(--spiro-fg-default);
  text-decoration: none;
  border-radius: 6px;
  margin-right: 12px;
}
.sidebar a:hover { background: var(--spiro-bg-subtle); }
.sidebar a.is-active {
  background: var(--spiro-bg-subtle);
  color: var(--spiro-fg-default);
  font-weight: 500;
  box-shadow: inset 2px 0 0 var(--spiro-accent-default);
}

/* ===== Main content ===== */
.main {
  padding: 40px 48px 120px 48px;
  max-width: 1120px;
  min-width: 0;
  margin: 0 auto;  /* centre the content column horizontally in the viewport */
}
.sect {
  padding: 24px 0 40px 0;
  border-bottom: 1px solid var(--spiro-border-subtle);
}
.sect:last-child { border-bottom: 0; }
.sect > h2 { margin-bottom: 4px; }
.sect__anchor {
  scroll-margin-top: 72px;  /* push past sticky nav */
}

/* ===== Hero ===== */
/*
 * Mesh-gradient hero card with a mouse-reactive blue glow, a static volt
 * sparkle in the upper-right, a deep brand-blue pool in the lower-left,
 * and a slow ambient hue-shift animation. Rounded 24px corners. Volt logo
 * top-left, display-72 title underneath, subtitle in muted cream, stats
 * as light outlined pills along the bottom.
 */
.hero {
  position: relative;
  isolation: isolate;
  margin: 0 0 40px 0;
  padding: 64px 56px 64px 56px;
  background: var(--spiro-bg-navy-950);
  color: var(--spiro-bg-cream-25);
  border-radius: 24px;
  overflow: hidden;
  scroll-margin-top: 72px;
}
/* Mesh gradient layer — sits behind content, doesn't intercept clicks.
   Custom properties --mx, --my track the cursor position (0%–100%);
   they fall back to a comfortable starting position before mouse moves. */
.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background:
    /* mouse-reactive brand-blue spotlight — follows the cursor */
    radial-gradient(circle 620px at var(--mx, 28%) var(--my, 28%),
      rgba(48, 56, 252, 0.45) 0%,
      rgba(48, 56, 252, 0.12) 35%,
      transparent 60%),
    /* fixed volt sparkle, upper-right */
    radial-gradient(circle 380px at 88% 12%,
      rgba(223, 255, 4, 0.18) 0%,
      rgba(223, 255, 4, 0.04) 40%,
      transparent 60%),
    /* fixed deep-blue pool, lower-left */
    radial-gradient(circle 540px at 8% 92%,
      rgba(31, 39, 229, 0.55) 0%,
      rgba(24, 30, 184, 0.20) 40%,
      transparent 65%),
    /* subtle complementary coral wash, lower-right — adds warmth */
    radial-gradient(circle 460px at 96% 90%,
      rgba(248, 113, 113, 0.08) 0%,
      transparent 55%),
    /* base diagonal */
    linear-gradient(135deg, #0F0E25 0%, #1A1833 50%, #181EB8 100%);
  transition: background 250ms ease-out;
  animation: hero-drift 18s ease-in-out infinite alternate;
}
@keyframes hero-drift {
  0%   { filter: hue-rotate(0deg)  brightness(1)    saturate(1); }
  50%  { filter: hue-rotate(-8deg) brightness(1.06) saturate(1.08); }
  100% { filter: hue-rotate(6deg)  brightness(0.98) saturate(0.95); }
}
@media (prefers-reduced-motion: reduce) {
  .hero::before { animation: none; transition: none; }
}
.hero__logo {
  display: block;
  width: 152px;
  height: auto;
  margin-bottom: 40px;
  color: var(--spiro-color-volt-500);  /* inline SVG paths use currentColor — volt pop on navy */
}
.hero__logo svg path { fill: currentColor; }

.hero__title {
  font-family: var(--spiro-font-display);
  font-weight: 600;
  font-size: 72px;
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 0 0 16px 0;
  color: var(--spiro-bg-cream-25);
  max-width: 18ch;
}

/* Interactive name cycler — click to try other names.
   Subtle underline appears on hover; cursor signals interactivity. */
.ds-name {
  position: relative;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  transition: color var(--spiro-duration-fast, 120ms) var(--spiro-easing-standard, ease);
}
.ds-name::after {
  content: "";
  position: absolute;
  left: 2px; right: 2px; bottom: 6px;
  height: 3px;
  background: currentColor;
  opacity: 0;
  border-radius: 2px;
  transition: opacity var(--spiro-duration-fast, 120ms) var(--spiro-easing-standard, ease);
}
.ds-name:hover::after,
.ds-name:focus-visible::after { opacity: 0.35; }
.ds-name:focus-visible { outline: none; }
.hero__sub {
  font-family: var(--spiro-font-sans);
  font-size: 18px;
  line-height: 1.55;
  letter-spacing: -0.02em;
  color: rgba(251,250,247,0.72);
  max-width: 64ch;
  margin: 0 0 40px 0;
}
.hero__pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  position: relative;
  z-index: 1;
}
.hero__pill {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 9999px;
  border: 1px solid rgba(251,250,247,0.22);
  background: rgba(251,250,247,0.06);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.hero__pill-num {
  font-family: var(--spiro-font-display);
  font-weight: 600;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: var(--spiro-bg-cream-25);
}
.hero__pill-label {
  font-family: var(--spiro-font-sans);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(251,250,247,0.72);
}

/* ===== Ramps / palette ===== */
.ramp {
  padding: 16px 0;
  border-bottom: 1px solid var(--spiro-border-subtle);
}
.ramp:last-child { border-bottom: 0; }
.ramp__meta { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
.ramp__name { font-size: 14px; font-weight: 600; text-transform: capitalize; display: inline-flex; gap: 4px; align-items: baseline; }
.ramp__note { font-size: 12px; color: var(--spiro-fg-muted); }
.star       { color: var(--spiro-accent-default); font-size: 12px; }
.ramp__cells {
  display: grid;
  grid-template-columns: repeat(13, 1fr);
  gap: 4px;
}
.swatch {
  appearance: none; border: 0; padding: 0;
  height: 64px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 6px 8px;
  font-size: 10px;
  text-align: left;
  transition: transform 120ms, box-shadow 120ms;
  /* Label colour is set inline per-swatch by build_preview.py using WCAG
     luminance; subtle inner highlight gives the edge a hairline of depth
     without an explicit border. */
  box-shadow: inset 0 0 0 1px rgba(15,14,37,0.04);
}
.swatch:hover { transform: translateY(-1px); box-shadow: var(--spiro-shadow-sm); }
.swatch__step { font-weight: 600; display: inline-flex; gap: 4px; align-items: center; }
.swatch__hex  { font-family: var(--spiro-font-mono); opacity: 0.75; font-size: 9.5px; }
.swatch .mark         { font-size: 10px; line-height: 1; opacity: 0.9; }
.swatch .mark--anchor { font-size: 11px; }
.swatch .mark--used   { font-size: 7px; opacity: 0.75; }

/* ===== Backgrounds ===== */
.bg-row { margin-bottom: 20px; }
.bg-row__name { margin: 0 0 8px 0; font-size: 14px; font-weight: 600; text-transform: capitalize;
                color: var(--spiro-fg-muted); }
.bg-row__cells { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
.bg-swatch {
  appearance: none; border: 1px solid var(--spiro-border-subtle);
  border-radius: 10px;
  padding: 16px;
  min-height: 88px;
  text-align: left;
  color: var(--spiro-fg-default);
  cursor: pointer;
  display: flex; flex-direction: column; justify-content: space-between;
  position: relative;
}
.bg-swatch:hover { box-shadow: var(--spiro-shadow-sm); }
.bg-swatch__step { font-size: 12px; font-weight: 600; opacity: 0.75; }
.bg-swatch__hex  { font-size: 11px; background: rgba(255,255,255,0.65); padding: 2px 6px; border-radius: 4px; align-self: flex-start; }
[data-theme='dark'] .bg-swatch__hex { background: rgba(0,0,0,0.4); color: var(--spiro-fg-default); }

/* ===== Typography table ===== */
.t-table { width: 100%; border-collapse: collapse; table-layout: auto; }
.t-table thead th {
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--spiro-fg-muted);
  font-weight: 600;
  padding: 10px 12px;
  border-bottom: 1px solid var(--spiro-border-default);
}
.t-table__group td {
  padding: 16px 12px 6px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--spiro-fg-muted);
  font-weight: 600;
  border-top: 1px solid var(--spiro-border-subtle);
  background: var(--spiro-bg-subtle);
}
.t-table__row td {
  padding: 14px 12px;
  vertical-align: middle;
  border-bottom: 1px solid var(--spiro-border-subtle);
  font-size: 12px;
  color: var(--spiro-fg-muted);
}
.t-table__token { width: 120px; }
.t-table__sample {
  width: 1%;          /* shrink to content, letting meta columns size themselves */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 420px;
}
.t-table__meta { white-space: nowrap; }
.t-table__meta.mono { font-family: var(--spiro-font-mono); }

/* Sample role styles.
   The `.t-sample` itself carries the colour — otherwise the `.t-table__row
   td` rule (specificity 0,1,1) would beat `.t-table__sample` (0,1,0) and
   muddy every sample with fg-muted. */
.t-sample { display: inline-block; color: var(--spiro-fg-default); }
/* Display — Clash Grotesk Semibold, -2% tracking */
.t-sample--display-72 { font-family: var(--spiro-font-display); font-weight: 600; font-size: 72px; line-height: 1.05; }
.t-sample--display-56 { font-family: var(--spiro-font-display); font-weight: 600; font-size: 56px; line-height: 1.08; }
.t-sample--display-44 { font-family: var(--spiro-font-display); font-weight: 600; font-size: 44px; line-height: 1.10; }
.t-sample--display-36 { font-family: var(--spiro-font-display); font-weight: 600; font-size: 36px; line-height: 1.15; }
.t-sample--display-30 { font-family: var(--spiro-font-display); font-weight: 600; font-size: 30px; line-height: 1.20; }
/* Heading — DM Sans SemiBold, -2% tracking */
.t-sample--heading-40 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 40px; line-height: 1.15; }
.t-sample--heading-36 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 36px; line-height: 1.20; }
.t-sample--heading-30 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 30px; line-height: 1.25; }
.t-sample--heading-28 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 28px; line-height: 1.27; }
.t-sample--heading-24 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 24px; line-height: 1.30; }
.t-sample--heading-20 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 20px; line-height: 1.35; }
.t-sample--heading-18 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 18px; line-height: 1.40; }
.t-sample--heading-16 { font-family: var(--spiro-font-sans);    font-weight: 600; font-size: 16px; line-height: 1.40; }
/* Body — DM Sans Regular */
.t-sample--body-24    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 24px; line-height: 1.50; }
.t-sample--body-20    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 20px; line-height: 1.50; }
.t-sample--body-18    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 18px; line-height: 1.55; }
.t-sample--body-16    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 16px; line-height: 1.50; }
.t-sample--body-14    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 14px; line-height: 1.50; }
.t-sample--body-12    { font-family: var(--spiro-font-sans);    font-weight: 400; font-size: 12px; line-height: 1.50; }
/* Label — DM Sans SemiBold, 0% tracking, ALL CAPS */
.t-sample--label-18   { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 18px; line-height: 1.10; letter-spacing: 0; text-transform: uppercase; }
.t-sample--label-14   { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 14px; line-height: 1.10; letter-spacing: 0; text-transform: uppercase; }
.t-sample--label-12   { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 12px; line-height: 1.10; letter-spacing: 0; text-transform: uppercase; }
/* Button — DM Sans SemiBold */
.t-sample--button-20  { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 20px; line-height: 1.0; }
.t-sample--button-18  { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 18px; line-height: 1.0; }
.t-sample--button-16  { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 16px; line-height: 1.0; }
/* Quote — Kalam (Regular for 24/36, Bold for 20) */
.t-sample--quote-36   { font-family: var(--spiro-font-accent); font-weight: 400; font-size: 36px; line-height: 1.30; }
.t-sample--quote-24   { font-family: var(--spiro-font-accent); font-weight: 400; font-size: 24px; line-height: 1.40; }
.t-sample--quote-20   { font-family: var(--spiro-font-accent); font-weight: 700; font-size: 20px; line-height: 1.40; }

/* ===== Scale tables (space / radius / border / shadow) ===== */
/* ===== Scale grids (Spacing / Radius / Borders / Shadows) ===== */
/* Each scale renders as a responsive card grid. Auto-fit means more
   columns appear on wide screens, fewer on narrow ones. Shadows get
   a slightly wider min-width so the soft-edge preview reads. */
.scale-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}
.scale-grid--shadow {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
.scale-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--spiro-bg-canvas);
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 12px;
}
.scale-card__preview {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}
.scale-card--shadow .scale-card__preview {
  min-height: 88px;
  background: var(--spiro-bg-subtle);
  border-radius: 8px;
}
[data-theme='dark'] .scale-card--shadow .scale-card__preview {
  background: var(--spiro-bg-muted);
}
.scale-card__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
}
.scale-card__value {
  font-size: 12px;
  color: var(--spiro-fg-muted);
}

.scale-table { width: 100%; border-collapse: collapse; }
.scale-table th, .scale-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--spiro-border-subtle);
  font-size: 13px;
  text-align: left;
  vertical-align: middle;
}
.scale-table th {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--spiro-fg-muted); font-weight: 600;
  border-bottom-color: var(--spiro-border-default);
}
.scale-table td:first-child { width: 140px; }
.scale-table td:nth-child(2) { width: 100px; color: var(--spiro-fg-muted); }

.space-bar   { display: inline-block; height: 12px; background: var(--spiro-accent-default); border-radius: 2px; }
/* Radius demo is a 80×80 square — once the short side is ≥ 2× the largest
   non-pill radius (32), every step shows its actual corner curve and pill
   reads as a perfect circle, not as a visually identical rounded rectangle. */
.radius-demo { display: inline-block; width: 80px; height: 80px;
               background: var(--spiro-bg-subtle);
               border: 1px solid var(--spiro-border-strong); }
.border-demo { display: inline-block; width: 72px; height: 40px; background: var(--spiro-bg-canvas);
               border-style: solid; border-color: var(--spiro-border-strong); border-radius: 4px; }
.border-demo--zero { width: auto; padding: 0 12px; border: 1px dashed var(--spiro-border-default);
                     color: var(--spiro-fg-muted); font-family: var(--spiro-font-mono);
                     font-size: 11px; display: inline-flex; align-items: center; }
/* Shadow demo: bigger tile + bright bg + spacing so the cast shadow is
   readable in both light and dark mode. The shadow ramp is best read
   against a contrasting surface, not its own colour. */
/* Shadow demo: pure-white tile on a cream-tinted backdrop so the shadow
   has somewhere to fall and the tile silhouette stays visible regardless
   of shadow strength. In dark mode, switch to a lighter zinc tile so
   the shadow's higher-alpha black ramp reads against the navy canvas. */
.shadow-cell {
  display: inline-block;
  padding: 18px 24px;
  border-radius: 12px;
  background: var(--spiro-bg-subtle);
}
.shadow-demo {
  display: inline-block; width: 96px; height: 56px;
  background: #FFFFFF;
  border-radius: 8px;
}
[data-theme='dark'] .shadow-cell { background: var(--spiro-bg-canvas); }
[data-theme='dark'] .shadow-demo { background: var(--spiro-color-zinc-200); }

/* ===== Semantic tokens table ===== */
.sem-table { width: 100%; border-collapse: collapse; }
.sem-table th { text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
                color: var(--spiro-fg-muted); font-weight: 600; padding: 10px 12px;
                border-bottom: 1px solid var(--spiro-border-default); }
.sem-table td { padding: 10px 12px; border-bottom: 1px solid var(--spiro-border-subtle); font-size: 13px; vertical-align: middle; }
.sem-table__group td {
  padding: 16px 12px 6px 12px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--spiro-fg-muted); font-weight: 600;
  border-top: 1px solid var(--spiro-border-subtle);
  background: var(--spiro-bg-subtle);
}
.sem-table__note { color: var(--spiro-fg-muted); font-size: 12px; }
.sem-swatch {
  display: inline-block;
  width: 20px; height: 20px;
  border-radius: 5px;
  margin-right: 8px;
  vertical-align: middle;
  border: 1px solid var(--spiro-border-subtle);
  box-shadow: inset 0 0 0 1px rgba(15,14,37,0.04);
}

/* ===== Semantic tokens in context (mock UI) ===== */
.sem-preview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 24px;
  align-items: start;
}
.sem-preview__card {
  background: var(--spiro-bg-canvas);
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 14px;
  padding: 20px;
  box-shadow: var(--spiro-shadow-sm);
}
.sem-preview__card-head { margin-bottom: 14px; }
.sem-preview__eyebrow   { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
                          color: var(--spiro-fg-muted); font-weight: 600; }
.sem-preview__title     { font-family: var(--spiro-font-sans); font-weight: 600; font-size: 22px;
                          color: var(--spiro-fg-default); margin-top: 2px; }
.sem-preview__sub       { font-size: 13px; color: var(--spiro-fg-muted); margin-top: 2px; }
.sem-preview__divider   { height: 1px; background: var(--spiro-border-subtle); margin: 14px 0; }
.sem-preview__body p    { font-size: 14px; color: var(--spiro-fg-default); line-height: 1.5; }
.sem-preview__pill-row  { display: flex; gap: 8px; flex-wrap: wrap; margin: 14px 0; }
.sem-preview__pill      { font-size: 12px; padding: 3px 10px; border-radius: 999px;
                          font-weight: 500; color: var(--spiro-fg-on-accent); }
.sem-preview__pill--success { background: var(--spiro-success-default); }
.sem-preview__pill--warning { background: var(--spiro-warning-default); }
.sem-preview__pill--info    { background: var(--spiro-info-default); }
.sem-preview__pill--danger  { background: var(--spiro-danger-default); }
/* Tabs row exercising accent.selected / accent.deselected (new in v0.12) */
.sem-preview__tabs { display: flex; gap: 6px; margin: 14px 0; flex-wrap: wrap; }
.sem-preview__tab  { padding: 8px 16px; border-radius: 9999px;
                     font-size: 13px; font-weight: 600; font-family: var(--spiro-font-sans);
                     letter-spacing: var(--spiro-letter-tight); cursor: default; }
.sem-preview__tab--selected   { background: var(--spiro-accent-selected); color: var(--spiro-accent-selected-fg); }
.sem-preview__tab--deselected { background: var(--spiro-accent-deselected); color: var(--spiro-accent-deselected-fg); }
/* Decorative callout exercising decorative-bg / decorative-fg (lavender / violet) */
.sem-preview__deco {
  display: flex; align-items: center; gap: 12px;
  background: var(--spiro-decorative-bg-lavender-soft);
  color: var(--spiro-decorative-fg-violet-dark);
  border-radius: 12px; padding: 12px 16px; margin: 14px 0;
  font-size: 13px; line-height: 1.5;
}
.sem-preview__deco-dot { display: inline-block; width: 10px; height: 10px;
                         border-radius: 9999px; flex-shrink: 0; }
.sem-preview__input {
  display: flex; flex-direction: column; gap: 2px;
  border: 1px solid var(--spiro-border-default);
  border-radius: 8px;
  padding: 8px 12px;
  background: var(--spiro-bg-canvas);
  margin: 14px 0;
}
.sem-preview__input-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em;
                            color: var(--spiro-fg-muted); font-weight: 600; }
.sem-preview__input-value { font-size: 14px; color: var(--spiro-fg-default);
                            font-variant-numeric: tabular-nums; font-family: var(--spiro-font-mono); }
.sem-preview__actions { display: flex; gap: 8px; flex-wrap: wrap; }
.sem-preview__btn {
  appearance: none; border: 0; padding: 8px 14px; font-size: 13px; font-weight: 500;
  border-radius: 999px; cursor: pointer;
  font-family: var(--spiro-font-sans);
  letter-spacing: var(--spiro-letter-tight);
}
.sem-preview__btn--primary { background: var(--spiro-accent-default); color: var(--spiro-fg-on-accent); }
.sem-preview__btn--primary:hover { background: var(--spiro-accent-hover); }
.sem-preview__btn--ghost   { background: transparent; color: var(--spiro-fg-default);
                             border: 1px solid var(--spiro-border-default); }
.sem-preview__btn--ghost:hover   { background: var(--spiro-bg-subtle); }
.sem-preview__btn--danger  { background: var(--spiro-danger-default); color: var(--spiro-fg-on-accent); }
.sem-preview__btn--danger:hover  { background: var(--spiro-danger-hover); }
/* Hover reveals the token each element pulls from. Implemented via a
   CSS-only tooltip driven by `data-tk`. */
[data-tk] { position: relative; }
[data-tk]:hover::after {
  content: attr(data-tk);
  position: absolute;
  left: 0; top: calc(100% + 6px);
  /* Tooltip is always a dark pill with cream text, regardless of theme —
     `bg.inverse` / `fg.inverse` would flip with theme, which is wrong for
     a tooltip. We want consistent, readable contrast either way. */
  background: var(--spiro-bg-navy-950);
  color: var(--spiro-bg-cream-25);
  font-family: var(--spiro-font-mono);
  font-weight: 500;
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 6px;
  white-space: nowrap;
  z-index: 40;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.sem-preview__note {
  background: var(--spiro-bg-subtle);
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 12px;
  padding: 16px;
  font-size: 12px;
  color: var(--spiro-fg-muted);
  line-height: 1.55;
}
.sem-preview__note h4 {
  margin: 0 0 6px 0;
  color: var(--spiro-fg-default);
  font-size: 13px;
  text-transform: none;
  letter-spacing: 0;
}
.sem-preview__note p { margin: 0; }

/* ===== Full semantic token strip ===== */
.tk-strip { margin-top: 24px; }
.tk-strip__head {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--spiro-fg-muted); font-weight: 600;
  margin-bottom: 12px;
}
.tk-strip__group-title {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--spiro-fg-muted); font-weight: 600;
  margin: 16px 0 8px 0;
  padding-top: 12px;
  border-top: 1px solid var(--spiro-border-subtle);
}
.tk-strip__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}
.tk-tile {
  display: flex; flex-direction: column; gap: 6px;
  padding: 8px;
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 10px;
  background: var(--spiro-bg-canvas);
}
.tk-tile__label {
  font-family: var(--spiro-font-mono);
  font-size: 10.5px;
  color: var(--spiro-fg-muted);
  word-break: break-word;
}
.tk-surface {
  height: 44px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--spiro-font-display); font-weight: 600; font-size: 16px;
}
.tk-text {
  display: flex; align-items: center;
  height: 44px; padding: 0 10px;
  font-size: 14px;
  font-family: var(--spiro-font-sans);
}
.tk-text--on-accent, .tk-text--on-inverse {
  border-radius: 6px;
  font-weight: 500;
}
.tk-border {
  height: 44px;
  border-radius: 6px;
  border-width: 2px;
  border-style: solid;
  background: var(--spiro-bg-canvas);
}
.tk-fill {
  height: 44px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 500;
}
.tk-fill--soft { font-weight: 500; }

/* ===== Decorative section ===== */
.deco-h { margin: 24px 0 12px 0; font-size: 14px; font-weight: 600;
          color: var(--spiro-fg-default); display: flex; align-items: center; gap: 10px; }
.deco-h__count { font-size: 11px; color: var(--spiro-fg-muted); font-family: var(--spiro-font-mono); font-weight: 400; }
.deco-grid { display: grid; gap: 6px; margin-bottom: 24px; }
.deco-row {
  display: grid;
  grid-template-columns: 110px 1fr;
  align-items: center;
  gap: 12px;
}
.deco-row__name { font-family: var(--spiro-font-mono); font-size: 12px; color: var(--spiro-fg-muted); }
.deco-row__cells { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.deco-cell {
  appearance: none; border: 0; padding: 0;
  height: 44px; border-radius: 6px; cursor: pointer;
  text-align: left; font-size: 10px;
  display: flex; align-items: flex-end; justify-content: flex-start;
  padding: 6px 8px;
  color: rgba(0,0,0,0.6);
  font-family: var(--spiro-font-mono);
  box-shadow: inset 0 0 0 1px rgba(15,14,37,0.04);
  transition: transform 120ms;
}
.deco-cell:hover { transform: translateY(-1px); box-shadow: var(--spiro-shadow-sm); }
.deco-cell__tone { opacity: 0.7; }
[data-theme='dark'] .deco-cell { color: rgba(255,255,255,0.6); }

/* ===== Gradients section ===== */
.grad-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
.grad-cell {
  appearance: none; border: 1px solid var(--spiro-border-subtle);
  background: var(--spiro-bg-canvas);
  border-radius: 10px; padding: 0; cursor: pointer; overflow: hidden;
  display: flex; flex-direction: column;
}
.grad-cell:hover { box-shadow: var(--spiro-shadow-sm); }
.grad-cell__art { height: 80px; }
.grad-cell__meta { padding: 8px 10px; display: flex; flex-direction: column; gap: 2px; text-align: left; }
.grad-cell__name { font-family: var(--spiro-font-mono); font-size: 11px; color: var(--spiro-fg-default); }
.grad-cell__note { font-family: var(--spiro-font-mono); font-size: 10px; color: var(--spiro-fg-muted); }

/* ===== Component gallery ===== */
/*
 * Masonry-style layout via CSS multi-column. Each component is wrapped in
 * a .cg-card and the parent .cg-masonry breaks the cards into 2–3 columns
 * based on viewport. break-inside: avoid keeps each card intact.
 */
.cg-masonry {
  column-count: 2;
  column-gap: 20px;
}
@media (min-width: 1400px) {
  .cg-masonry { column-count: 3; }
}
@media (max-width: 900px) {
  .cg-masonry { column-count: 1; }
}
.cg-card {
  break-inside: avoid;
  display: inline-block;
  width: 100%;
  margin-bottom: 20px;
  padding: 16px 18px 18px 18px;
  background: var(--spiro-bg-canvas);
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 12px;
}
.cg-h {
  margin: 0 0 12px 0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--spiro-fg-muted);
}
.cg-stack { display: flex; flex-direction: column; gap: 10px; margin-bottom: 0; align-items: flex-start; }
.cg-stack > * { width: auto; }
.cg-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; padding: 0;
          margin-bottom: 0; }
.cg-card .cg-row { padding: 0; border: 0; background: transparent; }

/* Chip mockups */
.cg-chip { padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;
           text-transform: uppercase; letter-spacing: 0.04em; font-family: var(--spiro-font-sans); }
.cg-chip--default { background: var(--spiro-bg-subtle); color: var(--spiro-fg-default); }
.cg-chip--selected { background: var(--spiro-accent-selected); color: var(--spiro-accent-selected-fg); }
.cg-chip--deselected { background: var(--spiro-accent-deselected); color: var(--spiro-accent-deselected-fg); }

/* Input mockups */
.cg-input { padding: 10px 14px; border-radius: 8px; background: var(--spiro-bg-canvas);
            border: 1px solid var(--spiro-border-default); font-size: 14px;
            color: var(--spiro-fg-muted); font-family: var(--spiro-font-sans);
            width: 280px; box-sizing: border-box; }
.cg-input--focus { border-color: var(--spiro-border-focus); border-width: 2px; padding: 9px 13px; }
.cg-input--error { border-color: var(--spiro-danger-default); color: var(--spiro-danger-default); }
.cg-input--disabled { opacity: 0.55; }

/* Badge */
.cg-badge { display: inline-flex; align-items: center; justify-content: center;
            min-width: 18px; height: 18px; padding: 0 6px; border-radius: 9999px;
            font-size: 11px; font-weight: 600; font-family: var(--spiro-font-sans); }

/* Switch */
.cg-switch { width: 36px; height: 20px; border-radius: 9999px; padding: 2px;
             display: flex; align-items: center; }
.cg-switch--off { background: var(--spiro-bg-muted); justify-content: flex-start; }
.cg-switch--on  { background: var(--spiro-accent-default); justify-content: flex-end; }
.cg-switch__thumb { width: 16px; height: 16px; border-radius: 9999px;
                    background: var(--spiro-fg-onAccent); }

/* Checkbox + Radio */
.cg-check { width: 18px; height: 18px; border-radius: 4px; display: inline-flex;
            align-items: center; justify-content: center; font-size: 12px;
            color: var(--spiro-fg-onAccent); font-weight: 700; }
.cg-check--unchecked { border: 1.5px solid var(--spiro-border-strong); background: transparent; }
.cg-check--checked, .cg-check--indeterminate { background: var(--spiro-accent-default); }
.cg-radio { width: 18px; height: 18px; border-radius: 9999px; box-sizing: border-box; }
.cg-radio--off { border: 1.5px solid var(--spiro-border-strong); }
.cg-radio--on  { border: 5px solid var(--spiro-accent-default); }

/* Tabs */
.cg-tab { padding: 12px 24px; border-radius: 9999px; font-size: 14px; font-weight: 600;
          font-family: var(--spiro-font-sans); cursor: pointer;
          letter-spacing: var(--spiro-letter-tight); }
.cg-tab--selected { background: var(--spiro-accent-selected); color: var(--spiro-accent-selected-fg); }
.cg-tab--deselected { background: var(--spiro-accent-deselected); color: var(--spiro-accent-deselected-fg); }

/* Alert */
.cg-alert { display: flex; flex-direction: column; gap: 4px; padding: 14px 16px;
            border-radius: 8px; border: 1px solid; max-width: 480px; box-sizing: border-box; }
.cg-alert__title { font-size: 16px; font-weight: 600; font-family: var(--spiro-font-sans); }
.cg-alert__body  { font-size: 14px; opacity: 0.9; }
.cg-alert--info    { background: var(--spiro-info-bg);    border-color: var(--spiro-info-default);    color: var(--spiro-info-fg); }
.cg-alert--success { background: var(--spiro-success-bg); border-color: var(--spiro-success-default); color: var(--spiro-success-fg); }
.cg-alert--warning { background: var(--spiro-warning-bg); border-color: var(--spiro-warning-default); color: var(--spiro-warning-fg); }
.cg-alert--danger  { background: var(--spiro-danger-bg);  border-color: var(--spiro-danger-default);  color: var(--spiro-danger-fg); }

/* Modal */
.cg-modal { background: var(--spiro-bg-canvas); border: 1px solid var(--spiro-border-subtle);
            border-radius: 16px; padding: 24px; max-width: 480px;
            box-shadow: var(--spiro-shadow-lg); display: flex; flex-direction: column; gap: 16px; }
.cg-modal__head { display: flex; justify-content: space-between; align-items: center; }
.cg-modal__title { font-size: 20px; font-weight: 600; font-family: var(--spiro-font-sans); color: var(--spiro-fg-default); }
.cg-modal__close { font-size: 18px; color: var(--spiro-fg-muted); cursor: pointer; }
.cg-modal__body { font-size: 16px; color: var(--spiro-fg-muted); line-height: 1.5; }
.cg-modal__actions { display: flex; gap: 12px; justify-content: flex-end; }

/* Dropdown */
.cg-dropdown { display: flex; align-items: center; justify-content: space-between;
               padding: 12px 16px; border-radius: 8px; background: var(--spiro-bg-canvas);
               border: 1px solid var(--spiro-border-default); font-size: 14px;
               color: var(--spiro-fg-muted); font-family: var(--spiro-font-sans); cursor: pointer;
               width: 280px; box-sizing: border-box; }
.cg-dropdown--focus { border-color: var(--spiro-border-focus); border-width: 2px; padding: 11px 15px; }
.cg-dropdown--disabled { opacity: 0.55; }
.cg-dropdown__chev { color: var(--spiro-fg-muted); }

/* Tooltip */
.cg-tooltip { display: inline-block; padding: 8px 12px; border-radius: 8px;
              background: var(--spiro-bg-navy-950); color: var(--spiro-bg-cream-25);
              font-size: 13px; font-family: var(--spiro-font-sans); }

/* Accordion */
.cg-accordion { background: var(--spiro-bg-canvas); border: 1px solid var(--spiro-border-subtle);
                border-radius: 8px; padding: 12px 16px;
                max-width: 480px; box-sizing: border-box; }
.cg-accordion__head { display: flex; justify-content: space-between; align-items: center;
                       font-weight: 600; font-size: 16px; color: var(--spiro-fg-default); }
.cg-accordion__chev { color: var(--spiro-fg-muted); }
.cg-accordion__body { margin-top: 12px; padding-top: 12px;
                       border-top: 1px solid var(--spiro-border-subtle);
                       font-size: 14px; color: var(--spiro-fg-muted); line-height: 1.5; }

/* Toast */
.cg-toast { display: flex; align-items: center; gap: 12px; padding: 12px 16px;
            border-radius: 8px; border: 1px solid; max-width: 480px;
            font-family: var(--spiro-font-sans); font-size: 14px; }
.cg-toast__icon  { font-size: 8px; }
.cg-toast__close { margin-left: auto; opacity: 0.7; cursor: pointer; }
.cg-toast--info    { background: var(--spiro-info-bg);    border-color: var(--spiro-info-default);    color: var(--spiro-info-fg); }
.cg-toast--success { background: var(--spiro-success-bg); border-color: var(--spiro-success-default); color: var(--spiro-success-fg); }
.cg-toast--warning { background: var(--spiro-warning-bg); border-color: var(--spiro-warning-default); color: var(--spiro-warning-fg); }
.cg-toast--danger  { background: var(--spiro-danger-bg);  border-color: var(--spiro-danger-default);  color: var(--spiro-danger-fg); }

/* ===== Prompts ===== */
.prompt-stack { display: flex; flex-direction: column; gap: 14px; }
.prompt-card {
  background: var(--spiro-bg-canvas);
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 12px;
  padding: 18px;
}
.prompt-card__head   { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; margin-bottom: 6px; }
.prompt-card__title  { margin: 0; font-size: 16px; font-weight: 600; color: var(--spiro-fg-default); }
.prompt-card__tags   { display: flex; gap: 6px; flex-wrap: wrap; }
.prompt-card__tag    { font-size: 10px; padding: 2px 8px; border-radius: 999px;
                       background: var(--spiro-bg-subtle); color: var(--spiro-fg-muted);
                       font-family: var(--spiro-font-mono); text-transform: uppercase; letter-spacing: 0.06em; }
.prompt-card__desc   { margin: 0 0 12px 0; font-size: 13px; color: var(--spiro-fg-muted); }
.prompt-card__body   { position: relative; }
.prompt-card__body pre {
  background: var(--spiro-bg-subtle);
  padding: 14px 16px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.55;
  max-height: 240px;
  overflow: auto;
  white-space: pre-wrap;
  color: var(--spiro-fg-default);
  font-family: var(--spiro-font-mono);
  margin: 0;
}
.prompt-card__copy   { position: absolute; top: 8px; right: 8px; z-index: 1; }

.prompt-empty {
  padding: 32px 24px;
  border: 1px dashed var(--spiro-border-default);
  border-radius: 12px;
  background: var(--spiro-bg-subtle);
  text-align: center;
  color: var(--spiro-fg-muted);
}
.prompt-empty__art   { font-size: 28px; color: var(--spiro-fg-muted); margin-bottom: 8px; }
.prompt-empty__title { font-weight: 600; font-size: 14px; color: var(--spiro-fg-default); margin-bottom: 6px; }
.prompt-empty__body  { margin: 0 auto; max-width: 48ch; font-size: 13px; }

/* ===== Copy chip ===== */
.copy-chip {
  appearance: none;
  background: transparent;
  border: 0;
  font-family: var(--spiro-font-mono);
  font-size: inherit;
  padding: 2px 6px;
  margin: -2px -6px;
  border-radius: 4px;
  color: inherit;
  cursor: pointer;
  text-align: left;
  line-height: inherit;
}
.copy-chip:hover { background: var(--spiro-bg-subtle); }
.copy-chip.is-copied { background: var(--spiro-success-default); color: var(--spiro-fg-on-accent); }
.swatch.is-copied { outline: 3px solid var(--spiro-success-default); outline-offset: 2px; }
.bg-swatch.is-copied { outline: 3px solid var(--spiro-success-default); outline-offset: 2px; }

/* ===== Buttons section ===== */
.btn-row {
  padding: 20px;
  border-radius: 12px;
  background: var(--spiro-bg-canvas);
  border: 1px solid var(--spiro-border-subtle);
  margin-bottom: 12px;
}
[data-theme='dark'] .btn-row { background: var(--spiro-bg-subtle); }
.btn-row--dark  { background: var(--spiro-bg-navy-950); color: var(--spiro-bg-cream-25); border-color: transparent; }
.btn-row--cream { background: var(--spiro-bg-cream-25); color: var(--spiro-bg-navy-950); border-color: var(--spiro-bg-cream-100); }
[data-theme='dark'] .btn-row--dark  { background: var(--spiro-bg-navy-950); }
[data-theme='dark'] .btn-row--cream { background: var(--spiro-bg-cream-25); color: var(--spiro-bg-navy-950); }
.btn-row__meta  { display: flex; gap: 12px; align-items: baseline; margin-bottom: 12px; }
.btn-row__name  { font-size: 11px; padding: 3px 8px; border-radius: 999px;
                  background: var(--spiro-bg-subtle); color: var(--spiro-fg-default); }
.btn-row--dark  .btn-row__name { background: rgba(255,255,255,0.1); color: var(--spiro-bg-cream-25); }
.btn-row--cream .btn-row__name { background: rgba(26,24,51,0.1); color: var(--spiro-bg-navy-950); }
.btn-row__desc  { font-size: 12px; color: var(--spiro-fg-muted); }
.btn-row--dark  .btn-row__desc { color: var(--spiro-color-zinc-300); }
.btn-row--cream .btn-row__desc { color: var(--spiro-color-zinc-700); }
.btn-row__cells, .btn-row__states {
  display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
}
.btn-row__states {
  margin-top: 12px; padding-top: 12px;
  border-top: 1px dashed var(--spiro-border-subtle);
}

/* ===== Icons / badges / patterns ===== */
.icon-grid    { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; }
.icon-cell    {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px 8px 8px;
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 10px;
  background: var(--spiro-bg-canvas);
  gap: 8px;
  margin: 0;
}
.icon-cell__art svg { width: 24px; height: 24px; color: var(--spiro-fg-default); }
.icon-cell figcaption { font-size: 11px; color: var(--spiro-fg-muted); font-family: var(--spiro-font-mono); }

.badge-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; }
.badge-cell {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 14px; border: 1px solid var(--spiro-border-subtle);
  border-radius: 10px; background: var(--spiro-bg-canvas);
  margin: 0;
}
.badge-cell__art svg { width: 56px; height: 56px; }
.badge-cell figcaption { font-size: 11px; color: var(--spiro-fg-muted); font-family: var(--spiro-font-mono); }

.pattern-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
.pattern-cell {
  position: relative;
  margin: 0;
  padding: 16px;
  border: 1px solid var(--spiro-border-subtle);
  border-radius: 10px;
  background: var(--spiro-bg-canvas);
  color: var(--p-light);
}
[data-theme='dark'] .pattern-cell { color: var(--p-dark); }
.pattern-cell__art svg { width: 100%; height: 120px; display: block; color: currentColor; }
.pattern-cell figcaption {
  margin-top: 8px;
  font-family: var(--spiro-font-mono);
  font-size: 11px;
  color: var(--spiro-fg-muted);
}

/* ===== Toast ===== */
.toast {
  position: fixed;
  bottom: 16px; left: 50%; transform: translateX(-50%);
  background: var(--spiro-bg-navy-950);
  color: var(--spiro-bg-cream-25);
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 999px;
  box-shadow: var(--spiro-shadow-lg);
  opacity: 0;
  transition: opacity 160ms ease-out;
  pointer-events: none;
  z-index: 50;
}
.toast.is-visible { opacity: 1; }

/* ===== Responsive ===== */
@media (max-width: 880px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .main { padding: 24px 20px 80px 20px; }
  .ramp__cells { grid-template-columns: repeat(7, 1fr); }
  .swatch { height: 52px; }
  .t-table__sample { max-width: 180px; }
  .t-sample--display-72, .t-sample--display-56, .t-sample--display-44 { font-size: 28px; }
  .t-sample--heading-40, .t-sample--heading-36 { font-size: 24px; }
}
"""

# ------------------------------------------------------------------
# Page template
# ------------------------------------------------------------------
PAGE = r"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Safari Design · v0.16</title>
<style>{fonts}</style>
<style>{tokens}</style>
<style>{buttons}</style>
<style>{app_css}</style>
</head>
<body>

<!-- ===== Top nav ===== -->
<nav class="nav" aria-label="Primary">
  <a href="#introduction" class="nav__brand">
    <span class="nav__logo" aria-hidden="true"></span>
    <span class="ds-name" role="button" tabindex="0" aria-label="Click to try other names">Safari</span> Design
  </a>
  <span class="nav__version">v0.16</span>
  <div class="nav__spacer"></div>
  <button id="themeToggle" class="nav__action" aria-label="Toggle colour theme">
    <span id="themeToggleLabel">Dark mode</span>
  </button>
</nav>

<div class="app">

  <!-- ===== Sidebar ===== -->
  <aside class="sidebar" aria-label="Sections">
    <div class="sidebar__group">
      <h4>Foundations</h4>
      <a href="#introduction">Introduction</a>
      <a href="#color-primitives">Color primitives</a>
      <a href="#typography">Typography</a>
      <a href="#spacing">Spacing</a>
      <a href="#radius">Radius</a>
      <a href="#borders">Borders</a>
      <a href="#shadows">Shadows</a>
    </div>
    <div class="sidebar__group">
      <h4>Tokens</h4>
      <a href="#semantic">Semantic</a>
      <a href="#decorative">Decorative</a>
      <a href="#gradients">Gradients</a>
      <a href="#semantic-preview">In context</a>
    </div>
    <div class="sidebar__group">
      <h4>Components</h4>
      <a href="#icons">Icons</a>
      <a href="#badges">Icon badges</a>
      <a href="#patterns">Patterns</a>
      <a href="#component-gallery">Gallery</a>
    </div>
    <div class="sidebar__group">
      <h4>Prompts</h4>
      <a href="#prompts">Prompts</a>
    </div>
  </aside>

  <!-- ===== Main ===== -->
  <main class="main">

    <!-- Hero -->
    <section id="introduction" class="hero sect__anchor">
      <span class="hero__logo" aria-label="Spiro">
        <svg width="152" height="61" viewBox="0 0 266 107" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M26.837 46.6173C20.4736 44.6507 14.9223 43.0325 14.9223 37.5946C14.9223 33.8924 17.8144 30.7695 22.4401 30.7695C27.4162 30.7695 30.0754 33.8924 30.6546 38.5202H42.6848C42.3365 27.1827 33.6622 19.7803 23.0193 19.7803C12.4939 19.7803 2.8921 27.3001 2.8921 38.6356C2.8921 45.9226 5.5533 52.7478 21.2837 57.7219C28.8035 60.1522 32.1574 63.0423 32.1574 67.4392C32.1574 72.6441 28.4552 76.2289 22.9039 76.2289C16.5425 76.2289 12.6094 72.2958 12.0302 64.5471H0C0 79.3539 11.1046 87.2181 22.673 87.2181C35.1649 87.2181 44.1876 79.121 44.1876 66.7445C44.1876 54.8298 35.8596 49.3939 26.837 46.6173Z"/>
          <path d="M88.0291 76.2299C75.5352 76.2299 66.2817 65.9354 66.2817 53.4415C66.2817 41.5268 75.5352 30.7685 87.5653 30.7685C100.406 30.7685 109.659 41.9905 109.659 53.6724C109.659 65.9354 100.406 76.2299 88.0291 76.2299ZM88.4909 19.7813C79.3528 19.7813 71.1403 23.597 65.7044 31.3477H65.4716V21.515H54.4844V107H66.5125V76.3454H66.7454C70.9094 83.286 79.5837 87.2191 89.301 87.2191C107.695 87.2191 121.691 72.4123 121.691 54.367C121.691 34.5861 107.577 19.7813 88.4909 19.7813Z"/>
          <path d="M133.836 14.1122H145.866V3.8147e-06H133.836V14.1122Z"/>
          <path d="M133.836 85.6005H145.866V21.5165H133.836V85.6005Z"/>
          <path d="M244.244 21.6115L242.242 20.7496V32.5847L242.919 33.0067C249.993 37.4195 254.216 45.021 254.216 53.339C254.216 66.5495 243.472 77.2938 230.264 77.2938C217.051 77.2938 206.303 66.5495 206.303 53.339C206.303 45.021 210.531 37.4175 217.61 33.0047L218.285 32.5828V20.7477L216.285 21.6095C203.254 27.2106 194.834 39.9892 194.834 54.167C194.834 67.8592 202.855 80.3949 215.306 86.2129L230.286 106.756L244.993 85.8129C255.347 80.1421 265.695 68.2274 265.695 54.167C265.695 39.9931 257.276 27.2146 244.244 21.6115Z"/>
          <path d="M172.816 27.2997H172.585V21.5155H161.363V85.5995H173.395V49.6244C173.395 38.8681 178.716 32.5047 189.126 32.1584V19.7819C180.682 20.2437 175.708 23.0183 172.816 27.2997Z"/>
          <path d="M230.263 54.9753C233.057 54.9753 235.325 52.6664 235.325 49.8201V19.6392C235.325 16.7909 233.057 14.484 230.263 14.484C227.468 14.484 225.201 16.7909 225.201 19.6392V49.8201C225.201 52.6664 227.468 54.9753 230.263 54.9753Z"/>
        </svg>
      </span>
      <h1 class="hero__title"><span class="ds-name" role="button" tabindex="0" aria-label="Click to try other names">Safari</span> Design</h1>
      <p class="hero__sub">
        The visual system behind Spiro — a pan-African electric motorcycle and battery-swap company.
        Primitives, components, icons, and patterns. Token-driven, theme-ready, WCAG-AA throughout.
      </p>
      <div class="hero__pills">
        <span class="hero__pill"><span class="hero__pill-num">15</span><span class="hero__pill-label">Colour families</span></span>
        <span class="hero__pill"><span class="hero__pill-num">13</span><span class="hero__pill-label">Steps per family</span></span>
        <span class="hero__pill"><span class="hero__pill-num">28</span><span class="hero__pill-label">Type roles</span></span>
        <span class="hero__pill"><span class="hero__pill-num">6</span><span class="hero__pill-label">Button variants</span></span>
        <span class="hero__pill"><span class="hero__pill-num">13</span><span class="hero__pill-label">Line icons</span></span>
        <span class="hero__pill"><span class="hero__pill-num">6</span><span class="hero__pill-label">Patterns</span></span>
      </div>
    </section>

    <!-- Color primitives -->
    <section id="color-primitives" class="sect sect__anchor">
      <h2>Color primitives</h2>
      <p class="eyebrow">
        15 chromatic families × 13 steps (25&nbsp;→&nbsp;975). Click any swatch to
        copy its hex. Brand anchors (blue·500, volt·500) are marked with <span class="star">★</span>.
      </p>
      {palette_rows}
    </section>

    <!-- Typography -->
    <section id="typography" class="sect sect__anchor">
      <h2>Typography</h2>
      <p class="eyebrow">
        Three families: Clash Grotesk (display), DM Sans (heading, body, label, button),
        Kalam (handwritten accent). Default tracking -2%.
      </p>
      {type_table}
    </section>

    <!-- Spacing -->
    <section id="spacing" class="sect sect__anchor">
      <h2>Spacing</h2>
      <p class="eyebrow">13-step scale. Used everywhere via <code>var(--spiro-space-*)</code>.</p>
      {space_table}
    </section>

    <!-- Radius -->
    <section id="radius" class="sect sect__anchor">
      <h2>Radius</h2>
      <p class="eyebrow">Nine steps plus <code>radius.pill</code> for fully-round shapes.</p>
      {radius_table}
    </section>

    <!-- Borders -->
    <section id="borders" class="sect sect__anchor">
      <h2>Border widths</h2>
      <p class="eyebrow">Four steps — default borders use 1px.</p>
      {border_table}
    </section>

    <!-- Shadows -->
    <section id="shadows" class="sect sect__anchor">
      <h2>Shadows</h2>
      <p class="eyebrow">Navy-tinted (rgba(15,14,37,α)) Tailwind-inspired ramp.</p>
      {shadow_table}
    </section>

    <!-- Icons -->
    <section id="icons" class="sect sect__anchor">
      <h2>Icons</h2>
      <p class="eyebrow">
        13 line icons, 24×24, 1.5px stroke. Colour inherits from <code>currentColor</code>.
      </p>
      <div class="icon-grid">{line_cells}</div>
    </section>

    <!-- Icon badges -->
    <section id="badges" class="sect sect__anchor">
      <h2>Icon badges</h2>
      <p class="eyebrow">
        Circular filled variants for editorial / marketing moments.
      </p>
      <div class="badge-grid">{badge_cells}</div>
    </section>

    <!-- Patterns -->
    <section id="patterns" class="sect sect__anchor">
      <h2>Patterns</h2>
      <p class="eyebrow">
        Afro-geometric decorative tiles. Strokes use <code>currentColor</code> — tints
        flip automatically in dark mode via <code>--p-light</code> / <code>--p-dark</code>.
      </p>
      <div class="pattern-grid">{pattern_cells}</div>
    </section>

    <!-- Semantic -->
    <section id="semantic" class="sect sect__anchor">
      <h2>Semantic tokens</h2>
      <p class="eyebrow">
        Abstractions on top of primitives. These are what components should reach for —
        they flip automatically with theme. Swatches show the resolved colour in each mode.
      </p>
      {semantic_table}
    </section>

    <!-- Decorative -->
    <section id="decorative" class="sect sect__anchor">
      <h2>Decorative tokens</h2>
      <p class="eyebrow">
        Mode-aware accent surfaces and accent foregrounds for editorial / illustration moments.
        Each family ships with three tones — soft / bold / dark — and flips intelligently across themes.
      </p>
      {decorative_section}
    </section>

    <!-- Gradients -->
    <section id="gradients" class="sect sect__anchor">
      <h2>Gradients</h2>
      <p class="eyebrow">
        Three solid feature gradients (full-bleed) plus alpha-fade gradients for layering.
        Drop a fade gradient as a fill layer over any solid surface to get a tinted overlay.
      </p>
      {gradients_section}
    </section>

    <!-- Component gallery — all 14 -->
    <section id="component-gallery" class="sect sect__anchor">
      <h2>Component gallery</h2>
      <p class="eyebrow">
        HTML mockups of each component using semantic tokens. Mirrors the Figma component set —
        flips with theme. Source of truth lives in Figma; these are reference renderings.
      </p>
      {component_gallery}
    </section>

    <!-- Semantic preview — tokens in real UI -->
    <section id="semantic-preview" class="sect sect__anchor">
      <h2>Semantic tokens in context</h2>
      <p class="eyebrow">
        A compact mock rendered purely from semantic tokens — same markup theme-flips
        without any styling overrides. Each element is annotated with the token it uses.
      </p>
      {semantic_preview}
    </section>

    <!-- Prompts -->
    <section id="prompts" class="sect sect__anchor">
      <h2>Prompts</h2>
      <p class="eyebrow">
        Reusable prompts for content generation (3D icons, marketing copy, alt text, etc.).
        This section is scaffolded and ready — prompts drop in via the <code>PROMPTS</code>
        list in <code>build_preview.py</code>.
      </p>
      {prompts_section}
    </section>

  </main>
</div>

<div id="toast" class="toast" role="status" aria-live="polite"></div>

<script>
(function () {{
  const root = document.documentElement;

  // ----- Theme toggle -----
  const toggleBtn = document.getElementById('themeToggle');
  const toggleLbl = document.getElementById('themeToggleLabel');
  function applyTheme(t) {{
    root.setAttribute('data-theme', t);
    toggleLbl.textContent = t === 'dark' ? 'Light mode' : 'Dark mode';
  }}
  toggleBtn.addEventListener('click', () => {{
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
  }});

  // ----- Hero mesh gradient — mouse-reactive spotlight -----
  // Track cursor position over the hero card; --mx, --my drive the
  // radial gradient origin in CSS. rAF-throttled to stay smooth.
  const hero = document.querySelector('.hero');
  if (hero && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
    let pending = null;
    hero.addEventListener('pointermove', (ev) => {{
      if (pending) return;
      pending = requestAnimationFrame(() => {{
        const r = hero.getBoundingClientRect();
        const mx = ((ev.clientX - r.left) / r.width) * 100;
        const my = ((ev.clientY - r.top) / r.height) * 100;
        hero.style.setProperty('--mx', `${{mx.toFixed(1)}}%`);
        hero.style.setProperty('--my', `${{my.toFixed(1)}}%`);
        pending = null;
      }});
    }});
    hero.addEventListener('pointerleave', () => {{
      hero.style.removeProperty('--mx');
      hero.style.removeProperty('--my');
    }});
  }}

  // ----- Name cycler — A/B testing the design system name in-context -----
  // Click any "Spiro <name>" instance to cycle through the candidates.
  // All instances stay in sync; the browser tab title updates too.
  const dsNames = ['Safari', 'Pulse', 'Atlas', 'Arc', 'Move'];
  let dsIdx = 0;
  const dsEls = document.querySelectorAll('.ds-name');
  function setDsName(name) {{
    dsEls.forEach(el => {{ el.textContent = name; }});
    document.title = `${{name}} Design · v0.16`;
  }}
  function cycleDs() {{
    dsIdx = (dsIdx + 1) % dsNames.length;
    setDsName(dsNames[dsIdx]);
  }}
  dsEls.forEach(el => {{
    el.addEventListener('click', (ev) => {{ ev.preventDefault(); cycleDs(); }});
    el.addEventListener('keydown', (ev) => {{
      if (ev.key === 'Enter' || ev.key === ' ') {{ ev.preventDefault(); cycleDs(); }}
    }});
  }});

  // ----- Resolve semantic swatch colours -----
  // Each .sem-swatch has data-var; --p-dark mirror uses a virtual root with
  // data-theme='dark' so we can resolve both columns at once.
  function resolveSwatch(el, theme) {{
    const v = el.getAttribute('data-var');
    if (!v) return;
    // Use a disposable probe to resolve the var in the requested theme.
    const probe = document.createElement('div');
    probe.setAttribute('data-theme', theme);
    probe.style.visibility = 'hidden';
    probe.style.position = 'fixed';
    probe.style.width = '0';
    probe.style.height = '0';
    probe.style.background = 'var(' + v + ')';
    document.body.appendChild(probe);
    const colour = getComputedStyle(probe).backgroundColor;
    document.body.removeChild(probe);
    el.style.background = colour;
  }}
  document.querySelectorAll('.sem-swatch').forEach(el => {{
    const forced = el.getAttribute('data-theme-force') || 'light';
    resolveSwatch(el, forced);
  }});

  // ----- Copy to clipboard -----
  const toast = document.getElementById('toast');
  let toastTimer = null;
  function showToast(msg) {{
    toast.textContent = msg;
    toast.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 1400);
  }}
  document.body.addEventListener('click', (ev) => {{
    const el = ev.target.closest('[data-copy]');
    if (!el) return;
    ev.preventDefault();
    const val = el.getAttribute('data-copy');
    if (!val) return;
    navigator.clipboard.writeText(val).then(() => {{
      el.classList.add('is-copied');
      setTimeout(() => el.classList.remove('is-copied'), 900);
      showToast('Copied ' + val);
    }}).catch(() => {{
      showToast('Copy failed');
    }});
  }});

  // ----- Success-flash demo for buttons -----
  document.querySelectorAll('[data-success-demo]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      btn.classList.add('spiro-btn--success');
      const label = btn.querySelector('.spiro-btn__label');
      const original = label ? label.textContent : null;
      if (label) label.textContent = 'Saved';
      setTimeout(() => {{
        btn.classList.remove('spiro-btn--success');
        if (label && original) label.textContent = original;
      }}, 1400);
    }});
  }});

  // ----- Sidebar active-section tracking -----
  const sections = Array.from(document.querySelectorAll('.sect__anchor'));
  const navLinks = Array.from(document.querySelectorAll('.sidebar a'));
  function linkFor(id) {{ return navLinks.find(a => a.getAttribute('href') === '#' + id); }}
  const io = new IntersectionObserver(entries => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        navLinks.forEach(a => a.classList.remove('is-active'));
        const link = linkFor(entry.target.id);
        if (link) link.classList.add('is-active');
      }}
    }});
  }}, {{ rootMargin: '-80px 0px -60% 0px', threshold: 0 }});
  sections.forEach(s => io.observe(s));
}})();
</script>
</body>
</html>
"""

# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------
def main():
    # Build the primitive→semantic usage map BEFORE rendering the palette so
    # palette_row can mark referenced swatches.
    _build_usage()

    palette_rows = "\n".join(palette_row(name, cols, note) for name, cols, note in FAMILIES)
    bg_rows = "\n".join(bg_row(k, v) for k, v in BACKGROUND.items())

    line_cells = "\n".join(icon_cell(p.stem, read_svg(p))
                           for p in sorted(ICON_DIR.glob("*.svg")))
    badge_cells = "\n".join(badge_cell(p.stem, read_svg(p))
                            for p in sorted(BADGE_DIR.glob("*.svg")))

    pattern_svgs = sorted(PATTERN_DIR.glob("*.svg"))
    pattern_cells_html = "\n".join(
        pattern_cell(p.stem, read_svg(p), PATTERN_CONFIG[i][0], PATTERN_CONFIG[i][1])
        for i, p in enumerate(pattern_svgs)
    )

    html = PAGE.format(
        fonts=FONTS_CSS,
        tokens=TOKENS_CSS,
        buttons=BTN_CSS,
        app_css=APP_CSS,
        palette_rows=palette_rows,
        bg_rows=bg_rows,
        type_table=type_table(),
        space_table=space_table(),
        radius_table=radius_table(),
        border_table=border_table(),
        shadow_table=shadow_table(),
        button_rows=button_rows(),
        line_cells=line_cells,
        badge_cells=badge_cells,
        pattern_cells=pattern_cells_html,
        semantic_table=semantic_table(),
        semantic_preview=semantic_preview(),
        decorative_section=decorative_section(),
        gradients_section=gradients_section(),
        component_gallery=component_gallery(),
        prompts_section=prompts_section(),
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} ({len(html)//1024} KB)")

if __name__ == "__main__":
    main()
