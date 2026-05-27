"""
Spiro v0.3 palette — single source of truth for Python generators.
13-step ramps (25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950, 975)
for 15 families plus a dedicated background family.
"""

STEPS = ["25", "50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950", "975"]

# Custom Spiro Blue — anchored to logo #3038FC
BLUE = ["#F6F7FF", "#EEF0FF", "#DADCFF", "#B7BEFE", "#8D98FD", "#5F6EFD",
        "#3038FC", "#1F27E5", "#181EB8", "#151A8F", "#10166B", "#080B3D", "#04061F"]

# Custom Spiro Volt — anchored to logo background #DFFF04
VOLT = ["#FDFFF2", "#FBFFE5", "#F4FFBE", "#ECFF8A", "#E6FF57", "#E2FF2C",
        "#DFFF04", "#C5E500", "#9EB800", "#7B8F00", "#5C6B00", "#2B3100", "#141800"]

# Tailwind-aligned families (50–950 standard; 25 and 975 extrapolated)
# Zinc replaces the previous Stone (warm taupe) — it sits near-neutral with a
# whisper of cool, so it harmonizes with both the warm cream canvas in light
# mode and the cool navy canvas in dark mode.
ZINC =  ["#FCFCFC", "#FAFAFA", "#F4F4F5", "#E4E4E7", "#D4D4D8", "#A1A1AA",
         "#71717A", "#52525B", "#3F3F46", "#27272A", "#18181B", "#09090B", "#040405"]
RED = ["#FEF8F8", "#FEF2F2", "#FEE2E2", "#FECACA", "#FCA5A5", "#F87171",
       "#EF4444", "#DC2626", "#B91C1C", "#991B1B", "#7F1D1D", "#450A0A", "#240505"]
ORANGE = ["#FFFBF6", "#FFF7ED", "#FFEDD5", "#FED7AA", "#FDBA74", "#FB923C",
          "#F97316", "#EA580C", "#C2410C", "#9A3412", "#7C2D12", "#431407", "#220A03"]
AMBER = ["#FFFDF5", "#FFFBEB", "#FEF3C7", "#FDE68A", "#FCD34D", "#FBBF24",
         "#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#451A03", "#240D01"]
YELLOW = ["#FEFDF3", "#FEFCE8", "#FEF9C3", "#FEF08A", "#FDE047", "#FACC15",
          "#EAB308", "#CA8A04", "#A16207", "#854D0E", "#713F12", "#422006", "#211002"]
LIME = ["#FAFFE8", "#F7FEE7", "#ECFCCB", "#D9F99D", "#BEF264", "#A3E635",
        "#84CC16", "#65A30D", "#4D7C0F", "#3F6212", "#365314", "#1A2E05", "#0D1702"]
EMERALD = ["#F3FEF8", "#ECFDF5", "#D1FAE5", "#A7F3D0", "#6EE7B7", "#34D399",
           "#10B981", "#059669", "#047857", "#065F46", "#064E3B", "#022C22", "#011610"]
CYAN = ["#F2FDFE", "#ECFEFF", "#CFFAFE", "#A5F3FC", "#67E8F9", "#22D3EE",
        "#06B6D4", "#0891B2", "#0E7490", "#155E75", "#164E63", "#083344", "#041B24"]
SKY = ["#F6FCFF", "#F0F9FF", "#E0F2FE", "#BAE6FD", "#7DD3FC", "#38BDF8",
       "#0EA5E9", "#0284C7", "#0369A1", "#075985", "#0C4A6E", "#082F49", "#041825"]
INDIGO = ["#F7F8FF", "#EEF2FF", "#E0E7FF", "#C7D2FE", "#A5B4FC", "#818CF8",
          "#6366F1", "#4F46E5", "#4338CA", "#3730A3", "#312E81", "#1E1B4B", "#0F0D25"]
VIOLET = ["#F9F7FF", "#F5F3FF", "#EDE9FE", "#DDD6FE", "#C4B5FD", "#A78BFA",
          "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#2E1065", "#170830"]
PINK = ["#FFF5FA", "#FDF2F8", "#FCE7F3", "#FBCFE8", "#F9A8D4", "#F472B6",
        "#EC4899", "#DB2777", "#BE185D", "#9D174D", "#831843", "#500724", "#280412"]
ROSE = ["#FFF6F7", "#FFF1F2", "#FFE4E6", "#FECDD3", "#FDA4AF", "#FB7185",
        "#F43F5E", "#E11D48", "#BE123C", "#9F1239", "#881337", "#4C0519", "#26020D"]

# Ordered for display: brand anchors first, neutral, then states/expansion
FAMILIES = [
    ("blue", BLUE, "Brand anchor — Spiro logo"),
    ("volt", VOLT, "Brand highlight — palette only (no UI surface)"),
    ("zinc", ZINC, "Neutral — text, borders"),
    ("red", RED, "Red — danger/alerts"),
    ("orange", ORANGE, "Orange — utility/bike imagery"),
    ("amber", AMBER, "Amber — warnings"),
    ("yellow", YELLOW, "Yellow"),
    ("lime", LIME, "Lime"),
    ("emerald", EMERALD, "Emerald — success/confirms"),
    ("cyan", CYAN, "Cyan"),
    ("sky", SKY, "Sky — info/tips"),
    ("indigo", INDIGO, "Indigo — editorial"),
    ("violet", VIOLET, "Violet — decorative"),
    ("pink", PINK, "Pink"),
    ("rose", ROSE, "Rose"),
]

# Dedicated background family — structured by TINT → step
# Light backgrounds are slightly tinted off-whites that replace pure #FFF.
# Dark backgrounds are navy-tilted near-blacks that replace pure #000.
BACKGROUND = {
    "cream": {
        "25":  "#FBFAF7",  # default light canvas (replaces #FFFFFF)
        "50":  "#F6F4EE",  # subtle light surface
        "100": "#EEEBE1",  # muted light surface
    },
    "periwinkle": {
        "50":  "#E8EDF3",  # soft blue tinted section (desaturated to match live site)
        "100": "#DBE4ED",
    },
    "mint": {
        "50":  "#E9F2EC",  # soft green tinted section (desaturated)
        "100": "#DCE8DF",
    },
    "peach": {
        "50":  "#F1ECE3",  # soft peach tinted section (warmer beige)
        "100": "#E5D8C7",
    },
    "lavender": {
        "50":  "#F2F1F6",  # soft violet tinted section (near-neutral)
        "100": "#E5E3EB",
    },
    "navy": {
        "900": "#1A1833",  # deep navy surface
        "950": "#0F0E25",  # default dark canvas (replaces #000000)
        "975": "#070612",  # deepest navy — footer
    },
}
