#!/usr/bin/env python3
"""Generate the profile SVG assets. Edit the CONTENT section, then run."""

from html import escape
from math import cos, radians, sin
from pathlib import Path

# ---------------------------------------------------------------- CONTENT

TITLE_LEFT = "SAYCA"
TITLE_RIGHT = "LABS"
SUBTITLE = "FREELANCE OR HIRE ME for an internship or work-study"
VERSION = "OPEN TO WORK"
ROWS = [
    ("LEGAL INDIVIDUAL", "Sayca Jason FERONE"),
    ("LEGAL STRUCTURE", "Sayca Labs"),
    ("STACK ORDER", "Python, C/C++, SQL, (...)"),
    ("SKILLS ORDER", "Backend, AI, Data, Full-stack"),
    ("LOCATION", "Nice / Sophia-Antipolis, FRANCE"),
]

# name: (icon, title, description lines, footer, active)
CARDS = {
    "draft": ("pentagon", "DRAFT",
              ["Complete methods and tools for",
               "Systems & Software development"],
              "OPEN SOURCE | DevTools shipping", True),
    "ficanas": ("candles", "FICANAS",
                ["42 Nice correction points",
                 "economy as a live market graph"],
                "IN PROGRESS | 42 Nice module", False),
    "codexion": ("scroll", "COFFMAN CODEXION",
                 ["Deadlock-free threads in C,",
                  "FIFO and EDF schedulers"],
                 "42 NICE | C, POSIX threads", True),
    "noesis": ("graph", "NOESIS & BASSO",
               ["Knowledge gather-n-filter engine",
                "for AI agents with fewer tokens"],
               "PRIVATE R&D | AI-Hive incremental loop", False),
    "hexis": ("hexagon", "HEXIS HONEYCOMB",
              ["Synchronized/shared memory for",
               "an entire AI agentic hive-mind"],
              "PRIVATE R&D | AI-Hive living memory", False),
}

# ---------------------------------------------------------------- THEME

BG = "#1d3134"
GRID = "#264043"
PANEL = "#121212"
ROW = "#1c1c1c"
RED = "#d9302c"
INK = "#ececec"
MUTED = "#8a8a8a"
ICON = "#6e6e6e"
# "panel": dark panel only, no wallpaper. "grid": wallpaper, no panel.
HEADER_MODE = "panel"
FONT = "DejaVu Sans, Verdana, Segoe UI, Helvetica, Arial, sans-serif"

ICONS = {
    "briefcase": '<rect x="90" y="80" width="80" height="58" rx="4"/>'
                 '<path d="M115 80v-10h30v10M90 104h80"/>',
    "code": '<path d="M110 72l-26 28 26 28M150 72l26 28-26 28M140 62'
            'l-20 76"/>',
    "mail": '<rect x="88" y="72" width="84" height="56" rx="3"/>'
            '<path d="M90 76l40 30 40-30"/>',
    "cap": '<path d="M80 92l50-24 50 24-50 24zM100 103v18c20 14 40 14'
           ' 60 0v-18"/>',
    "pentagon": '<path d="M130 58l42 31-16 49h-52l-16-49z"/>'
                '<path d="M130 80l21 15-8 24h-26l-8-24z"/>',
    "graph": '<circle cx="100" cy="76" r="10"/><circle cx="162" cy="86"'
             ' r="10"/><circle cx="124" cy="132" r="10"/>'
             '<path d="M110 78l42 6M156 95l-25 29M104 86l15 37"/>',
    "hexagon": '<path d="M130 58l38 21v42l-38 21-38-21v-42z"/>'
               '<path d="M130 82l17 9v18l-17 9-17-9v-18z"/>',
    "site": '<circle cx="130" cy="100" r="40"/>'
            '<ellipse cx="130" cy="100" rx="17" ry="40"/>'
            '<path d="M90 100h80M97 78h66M97 122h66"/>',
    "candles": '<path d="M100 60v80M130 70v66M160 64v70"/>'
               '<rect x="90" y="78" width="20" height="40"/>'
               '<rect x="120" y="96" width="20" height="26"/>'
               '<rect x="150" y="74" width="20" height="44"/>',
    "scroll": '<rect x="98" y="62" width="64" height="76" rx="3"/>'
              '<path d="M110 82h40M110 98h40M110 114h26"/>',
}


def hexagon(cx: float, cy: float, r: float) -> str:
    pts = [(cx + r * cos(radians(a)), cy + r * sin(radians(a)))
           for a in range(-90, 270, 60)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def logo(cx: float, cy: float, r: float) -> str:
    """Hexagonal cube: outer shell, concentric rings, six spokes."""
    rings = "".join(
        f'<polygon points="{hexagon(cx, cy, r * k)}" fill="none" '
        f'stroke="{INK}" stroke-width="{r * 0.05:.1f}"/>'
        for k in (0.52, 0.22)
    )
    spokes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="{INK}" '
        f'stroke-width="{r * 0.06:.1f}"/>'
        for x, y in (p.split(",") for p in hexagon(cx, cy, r * 0.84)
                     .split())
    )
    return (
        f'<polygon points="{hexagon(cx, cy, r * 0.92)}" fill="#000000" '
        f'stroke="{INK}" stroke-width="{r * 0.16:.1f}" '
        f'stroke-linejoin="round"/>{rings}{spokes}'
        f'<polygon points="{hexagon(cx, cy, r * 0.08)}" fill="{INK}"/>'
    )


def grid(w: int, h: int) -> str:
    return (
        f'<defs><pattern id="g" width="24" height="24" '
        f'patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" '
        f'stroke="{GRID}" stroke-width="1"/></pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="{BG}"/>'
        f'<rect width="{w}" height="{h}" fill="url(#g)"/>'
    )


def header(mode: str = HEADER_MODE) -> str:
    pw = 500
    w, px = (pw, 0) if mode == "panel" else (1000, 250)
    top = 185
    h = top + len(ROWS) * 52 + 60
    row_fill = ROW if mode == "panel" else PANEL
    rows = "".join(
        f'<rect x="{px + 28}" y="{top + i * 52}" width="{pw - 56}" '
        f'height="42" fill="{row_fill}"/>'
        f'<text x="{px + 42}" y="{top + i * 52 + 26}" font-size="12" '
        f'font-weight="bold" letter-spacing="2" fill="{RED}">{k}</text>'
        f'<text x="{px + pw - 42}" y="{top + i * 52 + 27}" font-size="16"'
        f' font-weight="bold" text-anchor="end" fill="{INK}">'
        f'{escape(v)}</text>'
        for i, (k, v) in enumerate(ROWS)
    )
    ground = (
        f'<rect width="{w}" height="{h}" fill="{PANEL}"/>'
        f'<rect width="{w}" height="5" fill="{RED}"/>'
        if mode == "panel"
        else grid(w, h) + f'<rect width="{w}" height="5" fill="{RED}"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">{ground}'
        f'{logo(px + pw / 2, 78, 46)}'
        f'<text x="{px + pw / 2 - 58}" y="92" font-size="38" '
        f'font-weight="bold" font-style="italic" text-anchor="end" '
        f'fill="{INK}">{TITLE_LEFT}</text>'
        f'<text x="{px + pw / 2 + 58}" y="92" font-size="38" '
        f'font-weight="bold" font-style="italic" fill="{INK}">'
        f'{TITLE_RIGHT}</text>'
        f'<text x="{px + pw // 2}" y="160" font-size="15" '
        f'textLength="{pw - 56}" lengthAdjust="spacingAndGlyphs" '
        f'font-weight="bold" font-style="italic" letter-spacing="1" '
        f'text-anchor="middle" fill="{INK}">'
        f'{escape(SUBTITLE)}</text>{rows}'
        f'<text x="{px + 28}" y="{h - 30}" font-size="13" '
        f'font-weight="bold" letter-spacing="2" fill="{MUTED}">'
        f'{VERSION}</text></svg>'
    )


def fit(text: str, per_char: float, avail: int = 228) -> str:
    """textLength attribute when the text would overflow the card."""
    if len(text) * per_char <= avail:
        return ""
    return f' textLength="{avail}" lengthAdjust="spacingAndGlyphs"'


def card(icon: str, title: str, lines: list[str], foot: str,
         active: bool) -> str:
    w, h = 260, 330
    bar = RED if active else "#555555"
    ink = INK if active else MUTED
    stripes = "".join(
        f'<rect y="{y}" width="{w}" height="2" fill="#1f1f1f"/>'
        for y in range(10, 200, 8)
    )
    desc = "".join(
        f'<text x="16" y="{264 + i * 20}" font-size="13.5" '
        f'fill="{ink}">{escape(t)}</text>'
        for i, t in enumerate(lines)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">'
        f'<rect width="{w}" height="{h}" fill="{PANEL}"/>'
        f'<rect width="{w}" height="200" fill="#181818"/>{stripes}'
        f'<rect width="{w}" height="5" fill="{bar}"/>'
        f'<g fill="none" stroke="{ICON}" stroke-width="6" '
        f'stroke-linejoin="round" stroke-linecap="round">{ICONS[icon]}</g>'
        f'<text x="16" y="238" font-size="17" font-weight="bold" '
        f'letter-spacing="3" fill="{ink}"{fit(title, 15)}>'
        f'{escape(title)}</text>{desc}'
        f'<text x="16" y="{h - 14}" font-size="12" font-weight="bold" '
        f'letter-spacing="1" fill="{RED if active else MUTED}"'
        f'{fit(foot, 9.3)}>'
        f'{escape(foot)}</text></svg>'
    )


def main() -> None:
    out = Path(__file__).parent
    (out / "header.svg").write_text(header() + "\n")
    for name, spec in CARDS.items():
        (out / f"card-{name}.svg").write_text(card(*spec) + "\n")


if __name__ == "__main__":
    main()
