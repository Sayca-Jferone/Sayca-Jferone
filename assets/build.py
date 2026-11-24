#!/usr/bin/env python3
"""Generate the profile plates: the saycalabs.com sea-chart charter as SVG.

Run: python3 assets/build.py   (needs fonttools and brotli)
Edit the CONTENT section, run, commit the SVG files.

Charter (saycalabs.design v1.0.0): night sea-chart ground, drawing plates
(hairline frame, corner ticks), Montserrat 800 italic on titles only, B612 and
B612 Mono for text, red = actions, green = states. Fonts are subset to the
glyphs each plate uses and embedded, so GitHub renders them from an <img>.
"""

import base64
import io
import json
from html import escape
from math import cos, radians, sin
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
W = 860

# ---------------------------------------------------------------- THEME

GROUND = "#192b2f"
GRATICULE = "rgba(130,175,182,0.14)"
CHART_LABEL = "rgba(170,200,206,0.60)"
PANEL = "#0d0d0d"
DEEP = "#050505"
ROW = "#191919"
RULE = "rgba(205,222,226,0.16)"
TICK = "rgba(205,222,226,0.60)"
ACCENT = "#e85454"
ON_ACCENT = "#0d0d0d"
INK = "#ffffff"
SOFT = "#cbcbcb"
MUTED = "#888888"
ICON = "#5d6c70"
STATE = "#4a9570"
TOP_A, TOP_B, SCAN = "#1f2c2f", "#101a1c", "#253335"

# font key -> (file, css family, weight, style, fallback)
FONTS = {
    "sig": ("montserrat-800-italic-latin.woff2", "SL Sig", 800, "italic",
            "Montserrat, 'Segoe UI', Helvetica, Arial, sans-serif"),
    "b": ("b612-400.woff2", "SL B612", 400, "normal",
          "'Segoe UI', Helvetica, Arial, sans-serif"),
    "bb": ("b612-700.woff2", "SL B612 Bold", 700, "normal",
           "'Segoe UI', Helvetica, Arial, sans-serif"),
    "m": ("b612-mono-400.woff2", "SL Mono", 400, "normal",
          "'DejaVu Sans Mono', Consolas, monospace"),
    "mb": ("b612-mono-700.woff2", "SL Mono Bold", 700, "normal",
           "'DejaVu Sans Mono', Consolas, monospace"),
}

# ---------------------------------------------------------------- CONTENT

HEADER_LEFT = [
    ("NAME", "Sayca Jason FERONE", False),
    ("STATE", "Open to work-study", True),
    ("STACK BY ORDER", "Python, C, C++, SQL, Rust...", False),
]
HEADER_RIGHT = [
    ("DOMAIN BY ORDER", "Backend, Data, AI, Full-stack...", False),
    ("BASE", "Nice / Sophia Antipolis", False),
    ("SCHOOL", "42 Nice, 42 Next", False),
]

CALLS = [
    ("call-hire", "briefcase", "HIRE ME",
     "Work-study or internship. Backend, data, AI engineering, full-stack.",
     "contract, start date, CV, FAQ", True),
    ("call-brief", "code", "BRIEF ME",
     "Freelance builds, specialised work, code and architecture audits.",
     "services, method, brief composer", False),
    ("call-read", "portrait", "READ ME",
     "What I master, what I am learning, what I can learn, where I aim.",
     "coverage map 2025-2030", False),
]

LOOKING = [
    ("CONTRACT", "Work-study or internship"),
    ("START", "February 2027"),
    ("RHYTHM", "35 h/week or more (work-study), flexible (internship)"),
    ("ROLES", "Backend, Data, AI, Full-stack..."),
    ("LOCATION", "Nice / Sophia Antipolis, remote"),
    ("PROGRAM", "42 Next, 2025-2030"),
]
GAIN = [
    ("Contracts before code",
     "Author of DRAFT, a public method that freezes requirements and "
     "invariants before implementation."),
    ("Strict by default",
     "Python under mypy --strict and Flake8, C under the 42 norm, mutation "
     "and random-campaign testing before a commit."),
    ("Team delivery",
     "Peer-reviewed 42 projects: a Go service, a C engine with event logs, "
     "a containerised infrastructure closed at full marks."),
    ("AI that stays engineered",
     "Built HEXIS, a memory and skill system that keeps LLM agents scoped, "
     "cheap and auditable."),
]

SERVICES = [
    ("GENERAL SOFTWARE", "Software your team can maintain.", "window",
     ["Backend & APIs", "CLI & automation", "Next-gen interactive web",
      "Static sites"]),
    ("SPECIALISED", "AI and systems work, with cost under control.", "chip",
     ["LLM integration", "Agent systems", "Low-level C",
      "Container infrastructure"]),
    ("AUDITS", "Proof, not opinions.", "lens",
     ["Code audit", "Architecture audit", "AI workflow audit"]),
]
STEPS = [
    ("D0", "BRIEF", "Your material, as it is"),
    ("D1", "REQUIREMENTS", "What must hold, signed off"),
    ("D2", "CONTRACT", "Invariants and interfaces"),
    ("BUILD", "BUILD", "Code that follows the contract"),
    ("D3", "AUDIT", "Proof, then handover"),
]

# name: (icon, title, description, footer, state, active)
PROJECTS = {
    "draft": ("pentagon", "DRAFT",
              "Complete methods and tools for Systems & Software "
              "development.", "OPEN SOURCE | DevTools shipping", True),
    "ficanas": ("candles", "FICANAS",
                "42 Nice correction points economy as a live market graph.",
                "IN PROGRESS | 42 Nice module", False),
    "codexion": ("scroll", "COFFMAN CODEXION",
                 "Deadlock-free threads in C, FIFO and EDF schedulers.",
                 "42 NICE | C, POSIX threads", True),
    "noesis": ("graph", "NOESIS & BASSO",
               "Knowledge gather-n-filter engine for AI agents with fewer "
               "tokens.", "PRIVATE R&D | AI-Hive incremental loop", False),
    "hexis": ("hexagon", "HEXIS HONEYCOMB",
              "Synchronized and shared memory for an entire AI agentic "
              "hive-mind.", "PRIVATE R&D | AI-Hive living memory", False),
}

LANES = [("sys", "SYSTEMS"), ("back", "BACKEND & DATA"), ("infra", "INFRA"),
         ("ai", "AI ENGINEERING"), ("arch", "ARCHITECTURE"),
         ("sec", "SECURITY"), ("web", "WEB")]
STATES = [("mastered", "MASTERED"), ("learning", "LEARNING"),
          ("canlearn", "CAN LEARN"), ("aspires", "ASPIRES")]

LOG = [
    ("2026-11-24", "saycalabs.com v2 redesign started"),
    ("2026-11", "Full-stack team project: requirements v0.1.0"),
    ("2026-10-29", "Containerised infrastructure project closed at full "
                   "marks"),
    ("2026-10-29", "saycalabs.com v1, static Astro"),
    ("2026-10", "Team service ported to Go"),
]
ASPIRATIONS = [
    ("Systems architect", "Own the contract layer of large systems, from "
                          "bare metal to agents."),
    ("Open research", "Publish the DRAFT method and its measurements as "
                      "papers."),
    ("Security audit", "Join audit and test practice to offensive "
                       "security."),
]

ICONS = {
    "briefcase": '<rect x="90" y="80" width="80" height="58" rx="2"/>'
                 '<path d="M115 80v-10h30v10M90 104h80"/>',
    "code": '<path d="M110 72l-26 28 26 28M150 72l26 28-26 28M140 62'
            'l-20 76"/>',
    "pentagon": '<path d="M130 58l42 31-16 49h-52l-16-49z"/>'
                '<path d="M130 80l21 15-8 24h-26l-8-24z"/>',
    "graph": '<circle cx="100" cy="76" r="10"/><circle cx="162" cy="86"'
             ' r="10"/><circle cx="124" cy="132" r="10"/>'
             '<path d="M110 78l42 6M156 95l-25 29M104 86l15 37"/>',
    "hexagon": '<path d="M130 58l38 21v42l-38 21-38-21v-42z"/>'
               '<path d="M130 82l17 9v18l-17 9-17-9v-18z"/>',
    "candles": '<path d="M100 60v80M130 70v66M160 64v70"/>'
               '<rect x="90" y="78" width="20" height="40"/>'
               '<rect x="120" y="96" width="20" height="26"/>'
               '<rect x="150" y="74" width="20" height="44"/>',
    "scroll": '<rect x="98" y="62" width="64" height="76" rx="2"/>'
              '<path d="M110 82h40M110 98h40M110 114h26"/>',
}
# 24x24 service glyphs (same drawings as the site)
GLYPHS = {
    "window": "M3 5h18v14H3zM3 9h18M9.5 12l-2 2.2 2 2.2M14.5 12l2 2.2-2 2.2",
    "chip": "M7 7h10v10H7zM10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4"
            "M17 10h4M17 14h4M10 10h4v4h-4z",
    "lens": "M10 4a6 6 0 1 0 0 12a6 6 0 1 0 0-12zM14.4 14.4L21 21"
            "M7.4 10l1.9 1.9 3.4-3.4",
}

# ---------------------------------------------------------------- FONTS

_metrics: dict[str, tuple[dict[int, int], int]] = {}


def metrics(key: str) -> tuple[dict[int, int], int]:
    if key not in _metrics:
        font = TTFont(HERE / "fonts" / FONTS[key][0])
        cmap = font.getBestCmap()
        hmtx = font["hmtx"]
        _metrics[key] = ({c: hmtx[g][0] for c, g in cmap.items()},
                         font["head"].unitsPerEm)
    return _metrics[key]


def width(s: str, key: str, size: float, ls: float = 0.0) -> float:
    adv, upm = metrics(key)
    return sum(adv.get(ord(c), upm * 0.55) for c in s) * size / upm \
        + ls * len(s)


def wrap(s: str, key: str, size: float, maxw: float, ls: float = 0.0
         ) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and width(trial, key, size, ls) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def font_css(key: str, chars: set[str]) -> str:
    fname, family, weight, style, _ = FONTS[key]
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = [1, 2]
    opts.notdef_outline = True
    font = subset.load_font(str(HERE / "fonts" / fname), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"font-style:{style};src:url(data:font/woff2;base64,{b64})"
            f"format('woff2')}}")


# ---------------------------------------------------------------- SVG

class Svg:
    def __init__(self, w: int, h: int, title: str) -> None:
        self.w, self.h, self.title = w, h, title
        self.body: list[str] = []
        self.used: dict[str, set[str]] = {}

    def add(self, s: str) -> None:
        self.body.append(s)

    def text(self, x: float, y: float, s: str, key: str, size: float,
             fill: str = INK, anchor: str = "start", ls: float = 0.0
             ) -> float:
        self.used.setdefault(key, set()).update(s)
        lsa = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{key}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"'
                 f'{lsa}>{escape(s)}</text>')
        return width(s, key, size, ls)

    def para(self, x: float, y: float, s: str, key: str, size: float,
             maxw: float, lead: float, fill: str = SOFT) -> float:
        lines = wrap(s, key, size, maxw)
        for i, line in enumerate(lines):
            self.text(x, y + i * lead, line, key, size, fill)
        return y + len(lines) * lead

    def render(self) -> str:
        css = "".join(font_css(k, c) for k, c in sorted(self.used.items()))
        cls = "".join(
            f".{k}{{font-family:'{FONTS[k][1]}',{FONTS[k][4]};"
            f"font-weight:{FONTS[k][2]};font-style:{FONTS[k][3]}}}"
            for k in FONTS)
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'role="img" aria-label="{escape(self.title)}">'
                f'<title>{escape(self.title)}</title>'
                f'<style>{css}{cls}</style>')
        return head + "".join(self.body) + "</svg>\n"


def ground(s: Svg, w: int, h: int) -> None:
    s.add(f'<rect width="{w}" height="{h}" fill="{GROUND}"/>')
    lines = "".join(
        f'<path d="M{x} 0V{h}" />' for x in range(0, w + 1, 72))
    lines += "".join(f'<path d="M0 {y}H{w}" />' for y in range(0, h + 1, 72))
    s.add(f'<g stroke="{GRATICULE}" stroke-width="1" fill="none">'
          f'{lines}</g>')
    s.add(f'<defs><radialGradient id="v" cx="50%" cy="50%" r="75%">'
          f'<stop offset="55%" stop-color="#04090a" stop-opacity="0"/>'
          f'<stop offset="100%" stop-color="#04090a" stop-opacity=".55"/>'
          f'</radialGradient></defs>'
          f'<rect width="{w}" height="{h}" fill="url(#v)"/>')


def plate(s: Svg, x: float, y: float, w: float, h: float,
          fill: str = PANEL) -> None:
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
          f'stroke="{RULE}" stroke-width="1"/>')
    t = 4
    k = 10
    corners = [
        f"M{x - t} {y + k}V{y - t}H{x + k}",
        f"M{x + w + t} {y + k}V{y - t}H{x + w - k}",
        f"M{x - t} {y + h - k}V{y + h + t}H{x + k}",
        f"M{x + w + t} {y + h - k}V{y + h + t}H{x + w - k}",
    ]
    s.add(f'<path d="{"".join(corners)}" fill="none" stroke="{TICK}" '
          f'stroke-width="1"/>')


def hexpts(cx: float, cy: float, r: float, scale_x: float = 1.0) -> str:
    return " ".join(
        f"{cx + r * cos(radians(a)) * scale_x:.2f},"
        f"{cy + r * sin(radians(a)):.2f}" for a in range(-90, 270, 60))


def emblem(s: Svg, cx: float, cy: float, k: float) -> None:
    """The hexagonal cube mark: nested hexagons joined by six spokes."""
    radii = [(95, 10), (42, 5), (19, 2.6), (8.5, 1.4), (3.8, 0.8)]
    spokes = [(95, 42, 6.5), (42, 19, 3.4), (19, 0, 1.4)]
    out = [f'<g fill="none" stroke="{INK}" stroke-linejoin="miter">']
    for r, sw in radii:
        out.append(f'<polygon points="{hexpts(cx, cy, r * k)}" '
                   f'stroke-width="{sw * k:.2f}"/>')
    for r1, r2, sw in spokes:
        for a in range(-90, 270, 60):
            c, sn = cos(radians(a)), sin(radians(a))
            out.append(
                f'<path d="M{cx + r1 * k * c:.2f} {cy + r1 * k * sn:.2f}'
                f'L{cx + r2 * k * c:.2f} {cy + r2 * k * sn:.2f}" '
                f'stroke-width="{sw * k:.2f}"/>')
    out.append("</g>")
    s.add("".join(out))


def kv(s: Svg, x: float, y: float, w: float, h: float, label: str,
       value: str, state: bool = False) -> None:
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{ROW}"/>')
    s.text(x + 12, y + 17, label, "m", 8.5, MUTED, ls=1.6)
    vx = x + 12
    if state:
        s.add(f'<circle cx="{vx + 3.5}" cy="{y + h - 15}" r="3.5" '
              f'fill="{STATE}"/>')
        vx += 14
    size = 13
    while width(value, "bb", size) > w - (vx - x) - 12:
        size -= 0.5
    s.text(vx, y + h - 11, value, "bb", size, INK)


def save(s: Svg, name: str) -> None:
    (HERE / f"{name}.svg").write_text(s.render(), encoding="ascii")


def sea_marks(s: Svg, w: int, h: int, pos: str) -> None:
    """Side ticks, a position in naval format and a 1 NM scale bar."""
    ticks = "".join(f'<path d="M0 {y}h6" />'
                    for y in range(18, h, 18)) + "".join(
        f'<path d="M{w} {y}h-6" />' for y in range(18, h, 18))
    s.add(f'<g stroke="{CHART_LABEL}" stroke-width="1">{ticks}</g>')
    s.text(12, 12, pos, "m", 8, CHART_LABEL, ls=1.2)
    s.add(f'<path d="M{w - 92} {h - 9}h72m0 -3v6m-72 -3v6" '
          f'stroke="{CHART_LABEL}" fill="none"/>')
    s.text(w - 96, h - 6, "1 NM", "m", 8, CHART_LABEL, "end", 1.2)


# ---------------------------------------------------------------- PLATES

def header() -> None:
    h = 252
    s = Svg(W, h, "Sayca Labs, Sayca Jason FERONE: name, state, stack, "
            "domains, base, school")
    ground(s, W, h)
    sea_marks(s, W, h, "43-42N 007-16E")
    plate(s, 20, 20, 820, 212)
    for i, (lab, val, st) in enumerate(HEADER_LEFT):
        kv(s, 40, 34 + i * 64, 230, 54, lab, val, st)
    for i, (lab, val, st) in enumerate(HEADER_RIGHT):
        kv(s, 590, 34 + i * 64, 230, 54, lab, val, st)
    emblem(s, 338, 126, 0.58)
    s.text(398, 120, "SAYCA", "sig", 40, INK, ls=1.2)
    s.text(398, 162, "LABS", "sig", 40, INK, ls=1.2)
    save(s, "header")


def icon_block(s: Svg, kind: str, x: float, y: float, w: float,
               h: float, color: str) -> None:
    gid = f"top{abs(hash((kind, x, y))) % 9999}"
    s.add(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
          f'<stop offset="0" stop-color="{TOP_A}"/>'
          f'<stop offset="1" stop-color="{TOP_B}"/></linearGradient></defs>'
          f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
          f'fill="url(#{gid})"/>')
    s.add(f'<g stroke="{SCAN}" stroke-width="1" opacity=".7">' + "".join(
        f'<path d="M{x} {yy}h{w}"/>' for yy in range(int(y) + 4,
                                                       int(y + h), 6))
        + "</g>")
    if kind in ICONS:
        s.add(f'<g transform="translate({x + w / 2 - 130:.1f},'
              f'{y + h / 2 - 100:.1f})" fill="none" stroke="{color}" '
              f'stroke-width="3" stroke-linejoin="miter" '
              f'stroke-linecap="square">{ICONS[kind]}</g>')


def call_tile(name: str, icon: str, title: str, hint: str, go: str,
              primary: bool) -> None:
    w, h = 270, 318
    s = Svg(w, h, f"{title}: {hint} ({go})")
    ground(s, w, h)
    px, py, pw, ph = 10, 10, 250, 296
    plate(s, px, py, pw, ph)
    shot_h = 150
    if icon == "portrait":
        b64 = base64.b64encode(
            (HERE / "img" / "portrait-tile.webp").read_bytes()).decode()
        s.add(f'<image x="{px}" y="{py}" width="{pw}" height="{shot_h}" '
              f'preserveAspectRatio="xMidYMid slice" '
              f'href="data:image/webp;base64,{b64}"/>')
        s.text(px + 12, py + shot_h - 12, "ID", "m", 8.5, SOFT, ls=1.6)
        s.text(px + pw - 12, py + shot_h - 12, "SAYCA-JFERONE", "mb", 8.5,
               INK, "end", 1.4)
    else:
        icon_block(s, icon, px, py, pw, shot_h, STATE if primary else ICON)
    if primary:
        fw = width("PRIORITY", "mb", 8.5, 1.4) + 16
        s.add(f'<rect x="{px + 10}" y="{py + 10}" width="{fw:.1f}" '
              f'height="17" fill="{STATE}"/>')
        s.text(px + 18, py + 22, "PRIORITY", "mb", 8.5, ON_ACCENT, ls=1.4)
    ty = py + shot_h + 34
    s.text(px + 16, ty, title, "sig", 19, INK, ls=0.6)
    y2 = s.para(px + 16, ty + 24, hint, "b", 11.5, pw - 32, 16)
    s.para(px + 16, y2 + 10, go, "m", 9.5, pw - 32, 14, ACCENT)
    save(s, name)


def section_title(name: str, text: str, tag: str) -> None:
    h = 62
    s = Svg(W, h, text)
    ground(s, W, h)
    s.text(24, 40, text, "sig", 27, INK, ls=0.8)
    s.add(f'<path d="M24 52H{W - 24}" stroke="{RULE}"/>')
    s.text(W - 24, 36, tag, "m", 9, CHART_LABEL, "end", 1.6)
    save(s, name)


def small_title(name: str, text: str) -> None:
    h = 44
    s = Svg(W, h, text)
    ground(s, W, h)
    s.text(24, 28, text, "mb", 10.5, SOFT, ls=3)
    s.add(f'<path d="M24 36H{W - 24}" stroke="{RULE}"/>')
    save(s, name)


def hire_panel() -> None:
    pw = 400
    s = Svg(W, 0, "")
    rows_h = 36
    left_h = 54 + len(LOOKING) * rows_h + 38
    right_y = 54
    for t, body in GAIN:
        right_y += 22 + len(wrap(body, "b", 11, pw - 40)) * 15 + 14
    h = max(left_h, right_y + 6) + 40
    s = Svg(W, h, "What I am looking for: " + "; ".join(
        f"{a} {b}" for a, b in LOOKING) + ". What you get: " + "; ".join(
        f"{a} - {b}" for a, b in GAIN))
    ground(s, W, h)
    plate(s, 20, 20, pw, h - 40)
    plate(s, 440, 20, pw, h - 40)
    s.text(40, 52, "What I am looking for", "bb", 14, INK)
    for i, (lab, val) in enumerate(LOOKING):
        y = 66 + i * rows_h
        s.add(f'<rect x="40" y="{y}" width="{pw - 40}" height="{rows_h - 6}"'
              f' fill="{ROW}"/>')
        s.text(52, y + 19, lab, "m", 8.5, MUTED, ls=1.6)
        size = 11.5
        while width(val, "bb", size) > pw - 40 - 12 - 92:
            size -= 0.5
        s.text(40 + pw - 40 - 12, y + 19, val, "bb", size, INK, "end")
    s.text(40, 66 + len(LOOKING) * rows_h + 18, "contact@saycalabs.com", "m",
           11, ACCENT)
    s.text(460, 52, "What you get", "bb", 14, INK)
    y = 66
    for t, body in GAIN:
        lines = wrap(body, "b", 11, pw - 56)
        bh = 22 + len(lines) * 15 + 6
        s.add(f'<rect x="460" y="{y}" width="{pw - 40}" height="{bh}" '
              f'fill="{ROW}"/>')
        s.text(472, y + 17, "+ " + t, "bb", 11.5, INK)
        for i, line in enumerate(lines):
            s.text(472, y + 34 + i * 15, line, "b", 11, SOFT)
        y += bh + 8
    save(s, "hire")


def services() -> None:
    cw, gap = 266, 11
    card_h = 40 + 34 + 4 * 30 + 18
    h = 20 + card_h + 14 + 70 + 20
    s = Svg(W, h, "Commission a system: general software, specialised work, "
            "audits; method D0 brief, D1 requirements, D2 contract, build, "
            "D3 audit")
    ground(s, W, h)
    for i, (title, line, glyph, tags) in enumerate(SERVICES):
        x = 20 + i * (cw + gap)
        plate(s, x, 20, cw, card_h)
        s.text(x + 16, 50, title, "sig", 15, INK, ls=0.6)
        s.add(f'<g transform="translate({x + cw - 40},34) scale(1)" '
              f'fill="none" stroke="{ACCENT}" stroke-width="1.1" '
              f'stroke-linecap="square"><path d="{GLYPHS[glyph]}"/></g>')
        s.para(x + 16, 74, line, "b", 11.5, cw - 32, 15)
        for j, tag in enumerate(tags):
            ty = 20 + 40 + 34 + j * 30
            s.add(f'<rect x="{x + 14}" y="{ty}" width="{cw - 28}" '
                  f'height="25" fill="{ROW}"/>')
            s.text(x + 26, ty + 17, tag, "bb", 11, INK)
    sy = 20 + card_h + 14
    sw = 156
    for i, (n, name, sub) in enumerate(STEPS):
        x = 20 + i * (sw + 10)
        plate(s, x, sy, sw, 70)
        s.text(x + 12, sy + 18, n, "m", 8.5, MUTED, ls=1.6)
        s.text(x + 12, sy + 36, name, "bb", 12, INK, ls=0.4)
        s.para(x + 12, sy + 54, sub, "b", 9.5, sw - 20, 12, SOFT)
    save(s, "services")


def project_card(name: str, icon: str, title: str, desc: str, foot: str,
                 active: bool) -> None:
    w, h = 270, 206
    s = Svg(W if False else w, h, f"{title}: {desc} ({foot})")
    ground(s, w, h)
    plate(s, 10, 10, 250, 186)
    s.add(f'<g transform="translate(-31,-10) scale(.62)" fill="none" '
          f'stroke="{ICON}" stroke-width="4.5" stroke-linejoin="miter" '
          f'stroke-linecap="square">{ICONS[icon]}</g>')
    s.text(30, 112, title, "sig", 16, INK, ls=0.6)
    s.para(30, 134, desc, "b", 11.5, 212, 15)
    s.add(f'<path d="M24 160H246" stroke="{RULE}"/>')
    dot = STATE if active else MUTED
    s.add(f'<circle cx="30" cy="177" r="3.2" fill="{dot}"/>')
    fs = 8.5
    while width(foot, "m", fs, 0.6) > 205:
        fs -= 0.25
    s.text(41, 180.5, foot, "m", fs, SOFT, ls=0.6)
    save(s, f"card-{name}")


def hexmark(s: Svg, cx: float, cy: float, r: float, state: str) -> None:
    pts = hexpts(cx, cy, r)
    if state == "mastered":
        s.add(f'<polygon points="{pts}" fill="{ACCENT}" stroke="{ACCENT}"/>')
    elif state == "learning":
        s.add(f'<polygon points="{pts}" fill="{PANEL}" stroke="{ACCENT}" '
              f'stroke-width="1.4"/><circle cx="{cx}" cy="{cy}" r="1.8" '
              f'fill="{ACCENT}"/>')
    elif state == "canlearn":
        s.add(f'<polygon points="{pts}" fill="{PANEL}" stroke="{SOFT}" '
              f'stroke-width="1.2" stroke-dasharray="3 2"/>')
    else:
        s.add(f'<polygon points="{pts}" fill="{PANEL}" stroke="{INK}" '
              f'stroke-width="1.2" stroke-dasharray="1 2.5"/>'
              f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="{INK}"/>')


def coverage() -> None:
    nodes = json.loads((HERE / "coverage.json").read_text())
    by: dict[str, list[dict[str, str]]] = {k: [] for k, _ in LANES}
    for n in nodes:
        by[n["lane"]].append(n)
    counts = {k: sum(1 for n in nodes if n["state"] == k) for k, _ in STATES}
    x0, maxw = 170, 660
    layouts: list[tuple[str, list[list[dict[str, str]]]]] = []
    navy = {"state": "mastered",
            "label": "French Navy (Marine Nationale) 2019 - 2025-07"}
    layouts.append(("DEFENCE", [[navy]]))
    for key, name in LANES:
        rows: list[list[dict[str, str]]] = [[]]
        used = 0.0
        for n in by[key]:
            cw = 22 + width(n["label"], "bb", 10.5) + 22
            if used + cw > maxw and rows[-1]:
                rows.append([])
                used = 0.0
            rows[-1].append(n)
            used += cw
        layouts.append((name, rows))
    top = 20 + 44
    total = sum(max(1, len(r)) * 26 + 14 for _, r in layouts)
    h = top + total + 52
    s = Svg(W, h, "Coverage map by domain: " + "; ".join(
        f"{n} {c}" for (_, n), c in zip(STATES, counts.values())))
    ground(s, W, h)
    plate(s, 20, 20, 820, h - 40)
    lx = 40
    for key, name in STATES:
        hexmark(s, lx + 6, 44, 6, key)
        lx += 20 + s.text(lx + 20, 48, f"{name} {counts[key]}", "mb", 9,
                          SOFT, ls=1.4) + 22
    y = top + 10
    for name, rows in layouts:
        rh = len(rows) * 26 + 14
        s.add(f'<rect x="32" y="{y - 6}" width="796" height="{rh - 6}" '
              f'fill="{ROW}"/>')
        s.text(44, y + 15, name, "mb", 9, MUTED, ls=1.6)
        for ri, row in enumerate(rows):
            x = x0
            for n in row:
                hexmark(s, x + 8, y + 11 + ri * 26, 6, n["state"])
                x += 22 + s.text(x + 22, y + 15 + ri * 26, n["label"], "bb",
                                 10.5, INK) + 16
        y += rh
    s.text(44, h - 34, "Coverage data under validation: dates are "
           "approximate. The dated, interactive map is on saycalabs.com.",
           "m", 8.5, MUTED, ls=0.4)
    save(s, "coverage")


def log_panel() -> None:
    pw = 400
    asp_h = sum(22 + len(wrap(b, "b", 11, pw - 56)) * 15 + 14
                for _, b in ASPIRATIONS)
    h = max(54 + len(LOG) * 34, 54 + asp_h) + 54
    s = Svg(W, h, "Recent log and aspirations")
    ground(s, W, h)
    plate(s, 20, 20, pw, h - 40)
    plate(s, 440, 20, pw, h - 40)
    s.text(40, 52, "Recent log", "bb", 14, INK)
    for i, (date, what) in enumerate(LOG):
        y = 66 + i * 34
        s.add(f'<rect x="40" y="{y}" width="{pw - 40}" height="28" '
              f'fill="{ROW}"/>')
        s.text(52, y + 18, date, "m", 9, MUTED)
        s.text(132, y + 18, what, "b", 10.5, INK)
    s.text(460, 52, "Aspirations", "bb", 14, INK)
    y = 66
    for t, body in ASPIRATIONS:
        lines = wrap(body, "b", 11, pw - 56)
        bh = 22 + len(lines) * 15 + 6
        s.add(f'<rect x="460" y="{y}" width="{pw - 40}" height="{bh}" '
              f'fill="{ROW}"/>')
        s.text(472, y + 17, "+ " + t, "bb", 11.5, INK)
        for i, line in enumerate(lines):
            s.text(472, y + 34 + i * 15, line, "b", 11, SOFT)
        y += bh + 8
    save(s, "log")


def footer() -> None:
    h = 112
    s = Svg(W, h, "Drawn by Sayca Jason FERONE, Sayca Labs independent, "
            "position 43-42N 007-16E")
    ground(s, W, h)
    sea_marks(s, W, h, "")
    plate(s, 20, 20, 820, 66)
    cells = [("DRAWN BY", "Sayca Jason FERONE", "bb"),
             ("STUDIO", "Sayca Labs, independent", "bb"),
             ("POSITION", "43-42N 007-16E", "mb"),
             ("FILES", "humans.txt llms.txt", "m")]
    cw = 820 / 4
    for i, (lab, val, key) in enumerate(cells):
        x = 20 + i * cw
        if i:
            s.add(f'<path d="M{x} 20V86" stroke="{RULE}"/>')
        s.text(x + 16, 46, lab, "m", 8.5, MUTED, ls=1.6)
        s.text(x + 16, 68, val, key, 11.5 if key != "m" else 9.5, INK)
    save(s, "footer")


def banner() -> None:
    """LinkedIn cover, 1584 x 396. Key content stays in x 400-1440:
    the avatar covers the lower left, the edit button the top right."""
    bw, bh = 1584, 396
    s = Svg(bw, bh, "Sayca Labs - Sayca Jason FERONE. Systems & Software "
            "engineering. Open to work-study. Nice / Sophia Antipolis.")
    ground(s, bw, bh)
    sea_marks(s, bw, bh, "43-42N 007-16E")
    plate(s, 400, 72, 1040, 252)
    emblem(s, 560, 198, 0.78)
    s.text(660, 196, "SAYCA", "sig", 84, INK, ls=2.5)
    s.text(660, 280, "LABS", "sig", 84, INK, ls=2.5)
    s.add(f'<path d="M1096 96V300" stroke="{RULE}"/>')
    rows = [("STATE", "Open to work-study", True),
            ("STACK BY ORDER", "Python, C, C++, SQL, Rust...", False),
            ("BASE", "Nice / Sophia Antipolis", False)]
    for i, (lab, val, st) in enumerate(rows):
        kv(s, 1120, 92 + i * 72, 296, 62, lab, val, st)
    s.text(660, 112, "SYSTEMS & SOFTWARE ENGINEERING", "mb", 11, SOFT,
           ls=3)
    s.text(1416, 351, "saycalabs.com", "m", 12, ACCENT, "end", 1.2)
    out = HERE / "linkedin"
    out.mkdir(exist_ok=True)
    (out / "banner.svg").write_text(s.render(), encoding="ascii")


FAQ = [
    ("Which contract and rhythm?",
     "Work-study (alternance) or internship, from February 2027. "
     "Work-study: 35 hours a week, more where the contract allows. "
     "Internship: flexible hours."),
    ("Which teams fit best?",
     "Backend and data teams first, then AI engineering and full-stack "
     "work. Anything where correctness is measured."),
    ("Can I see code?",
     "Most repositories are public under Apache 2.0 on "
     "github.com/sayca-jferone."),
]
METHOD = [
    ("No standard limitation",
     "I never reject a method because it is unusual: conventional "
     "judgement is what hides breakthrough solutions."),
    ("Contracts first",
     "Each unit is specified before it is built, so blocks assemble into "
     "a System that scales."),
    ("Keep what was learned",
     "Every hour of reasoning, human or AI, is captured in a reusable "
     "form instead of being lost."),
    ("Self-documenting projects",
     "Humans and AI agents share the same written sources of truth."),
]


def intro() -> None:
    s = Svg(W, 150, "")
    lead = ("Open to a 6-month internship or a 12-24 month work-study "
            "(alternance), from February 2027, Nice / Sophia Antipolis.")
    tail = ("Ex-French Navy sonar team leader. Author of DRAFT, an open "
            "systems method. I model a System before I code it.")
    s.title = lead + " " + tail
    ground(s, W, 150)
    plate(s, 20, 20, 820, 110)
    s.add(f'<circle cx="46" cy="49" r="4.5" fill="{STATE}"/>')
    s.text(60, 54, "Open to a 6-month internship or a 12-24 month "
           "work-study (alternance)", "bb", 14.5, INK)
    s.text(60, 76, "From February 2027 - Nice / Sophia Antipolis, remote "
           "possible", "b", 12.5, SOFT)
    s.add(f'<path d="M40 92H820" stroke="{RULE}"/>')
    s.para(40, 112, tail, "b", 12, 780, 16, SOFT)
    save(s, "intro")


def text_rows(name: str, title: str, rows: list[tuple[str, str]],
              lw: int, label_key: str = "bb") -> None:
    """Question/answer or principle/practice rows on one plate."""
    heights = [max(34, len(wrap(a, "b", 11, 820 - 60 - lw)) * 15 + 18)
               for _, a in rows]
    h = 40 + 24 + sum(h_ + 6 for h_ in heights) + 20
    s = Svg(W, h, title + ": " + " ".join(f"{q} {a}" for q, a in rows))
    ground(s, W, h)
    plate(s, 20, 20, 820, h - 40)
    y = 44
    for (q, a), rh in zip(rows, heights):
        s.add(f'<rect x="36" y="{y}" width="788" height="{rh}" '
              f'fill="{ROW}"/>')
        s.text(50, y + 21, q, label_key, 11.5, INK)
        for i, line in enumerate(wrap(a, "b", 11, 820 - 60 - lw)):
            s.text(50 + lw, y + 21 + i * 15, line, "b", 11, SOFT)
        y += rh + 6
    save(s, name)


def cta() -> None:
    s = Svg(W, 96, "Price on quote. Describe the need in the brief "
            "composer on saycalabs.com or write to contact@saycalabs.com")
    ground(s, W, 96)
    plate(s, 20, 20, 820, 56)
    s.text(40, 44, "PRICE", "m", 8.5, MUTED, ls=1.6)
    s.text(40, 62, "On quote", "bb", 13, INK)
    s.text(160, 44, "DESCRIBE THE NEED", "m", 8.5, MUTED, ls=1.6)
    s.text(160, 62, "Brief composer on saycalabs.com", "bb", 13, ACCENT)
    s.text(500, 44, "OR WRITE TO", "m", 8.5, MUTED, ls=1.6)
    s.text(500, 62, "contact@saycalabs.com", "bb", 13, INK)
    save(s, "cta")


def button(name: str, label: str, sub: str) -> None:
    w, h = 270, 76
    s = Svg(w, h, f"{label} - {sub}")
    ground(s, w, h)
    plate(s, 10, 10, 250, 56)
    s.text(135, 36, label, "sig", 14, INK, "middle", 0.8)
    s.text(135, 54, sub, "m", 8.5, ACCENT, "middle", 0.8)
    save(s, name)



def main() -> None:
    header()
    for c in CALLS:
        call_tile(*c)
    section_title("t-hire", "RECRUIT AN ENGINEER IN TRAINING", "01 HIRE")
    hire_panel()
    section_title("t-brief", "COMMISSION A SYSTEM", "02 BRIEF")
    services()
    section_title("t-read", "COVERAGE MAP", "03 READ")
    coverage()
    small_title("t-projects", "CURRENT PROJECTS")
    small_title("t-rnd", "CURRENT R&D")
    for name, args in PROJECTS.items():
        project_card(name, *args)
    small_title("t-log", "LOG & AIMS")
    log_panel()
    footer()
    intro()
    text_rows("faq", "Which contract, which teams, which code", FAQ, 190)
    text_rows("method", "How I work", METHOD, 190)
    cta()
    button("go-site", "SAYCALABS.COM", "portfolio, hire, brief")
    button("go-linkedin", "LINKEDIN", "linkedin.com/in/sayca")
    button("go-42", "42 CURRICULUM", "profile.intra.42.fr")
    button("go-ethics-en", "ETHICS CHARTER", "english document")
    button("go-ethics-fr", "CHARTE D'ETHIQUE", "french document")
    small_title("t-method", "HOW I WORK")
    small_title("t-elsewhere", "ELSEWHERE")
    banner()


if __name__ == "__main__":
    main()
