#!/usr/bin/env python3
"""Build MZtech logo assets (deterministic, no external services).

Concept: an M monogram whose middle stroke is a checkmark —
M for MZtech, the check for trust ("We don't build software. We build trust.").
Palette and type follow templates/proposal/deck.html.
Outputs SVG + PNG into this folder.
"""
import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FONT = ROOT / "templates/proposal/fonts/Poppins-600.woff2"

NAVY = "#282769"
BLUE = "#1a407e"
CYAN = "#178dc2"
SKY = "#16add8"
INK = "#101038"
WHITE = "#ffffff"

GRAD = (
    '<linearGradient id="check" gradientUnits="userSpaceOnUse" x1="24" y1="0" x2="96" y2="0">'
    f'<stop offset="0" stop-color="{CYAN}"/>'
    f'<stop offset="1" stop-color="{SKY}"/></linearGradient>'
)
# Pillar gradient: same navy->blue tones as the banner background.
# userSpaceOnUse is required: vertical strokes have a zero-width bounding box,
# which disables objectBoundingBox gradients.
PILLAR_GRAD = (
    '<linearGradient id="pillar" gradientUnits="userSpaceOnUse" x1="0" y1="22" x2="0" y2="96">'
    f'<stop offset="0" stop-color="{NAVY}"/>'
    f'<stop offset="1" stop-color="{BLUE}"/></linearGradient>'
)


def mark(pillar_stroke: str) -> str:
    """M monogram, 120x120 grid. Middle V is a checkmark (longer up-stroke)."""
    return (
        f'<g fill="none" stroke-width="15" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M24 96V30" stroke="{pillar_stroke}"/>'
        f'<path d="M96 96V22" stroke="{pillar_stroke}"/>'
        f'<path d="M24 30L56 66L96 22" stroke="url(#check)"/>'
        f"</g>"
    )


def wordmark(color: str, dot_color: str, size: float):
    """Outline 'MZtech' from Poppins 600. Returns (svg, width)."""
    font = TTFont(FONT)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    s = size / upm
    tracking = -0.02 * size  # tight, modern spacing
    x = 0.0
    parts = []
    for ch in "MZtech":
        gname = cmap[ord(ch)]
        pen = SVGPathPen(glyph_set)
        glyph_set[gname].draw(pen)
        d = pen.getCommands()
        parts.append(
            f'<path transform="translate({x:.2f},0) scale({s:.5f},{-s:.5f})" '
            f'd="{d}" fill="{color}"/>'
        )
        x += hmtx[gname][0] * s + tracking
    x -= tracking
    dot_r = 0.082 * size
    dot_cx = x + dot_r + 0.06 * size
    parts.append(f'<circle cx="{dot_cx:.2f}" cy="{-dot_r:.2f}" r="{dot_r:.2f}" fill="{dot_color}"/>')
    width = dot_cx + dot_r
    return "".join(parts), width


def svg_doc(w, h, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>'
    )


def render_png(svg_path: Path, png_path: Path, width: int):
    subprocess.run(
        ["rsvg-convert", "--format=png", f"--width={width}",
         f"--output={png_path}", str(svg_path)],
        check=True,
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Mark only (transparent)
    (OUT / "mark.svg").write_text(svg_doc(120, 120, mark("url(#pillar)"), GRAD + PILLAR_GRAD))
    render_png(OUT / "mark.svg", OUT / "mark.png", 1024)

    # 2. Horizontal lockup: mark + outlined wordmark, baseline aligned
    fs = 68
    wm, wm_w = wordmark(NAVY, CYAN, fs)
    pad, mark_size, gap = 24, 120, 34
    wm_x = pad + mark_size + gap
    baseline = pad + 92  # wordmark baseline sits near mark bottom
    h = pad * 2 + mark_size
    w = wm_x + wm_w + pad
    body = (
        f'<g transform="translate({pad},{pad})">{mark("url(#pillar)")}</g>'
        f'<g transform="translate({wm_x},{baseline})">{wm}</g>'
    )
    (OUT / "lockup.svg").write_text(svg_doc(round(w), h, body, GRAD + PILLAR_GRAD))
    render_png(OUT / "lockup.svg", OUT / "lockup.png", round(w * 3))

    # 3. Reversed lockup for dark backgrounds
    wm_r, _ = wordmark(WHITE, SKY, fs)
    body_r = (
        f'<g transform="translate({pad},{pad})">{mark(WHITE)}</g>'
        f'<g transform="translate({wm_x},{baseline})">{wm_r}</g>'
    )
    (OUT / "lockup-reversed.svg").write_text(svg_doc(round(w), h, body_r, GRAD))
    render_png(OUT / "lockup-reversed.svg", OUT / "lockup-reversed.png", round(w * 3))

    # 4. Avatar / app icon: navy-blue gradient tile, white pillars, gradient check
    tile = (
        '<linearGradient id="tile" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{NAVY}"/>'
        f'<stop offset="1" stop-color="{BLUE}"/></linearGradient>'
    )
    scale = 3.9
    off = (800 - 120 * scale) / 2
    body_a = (
        '<rect width="800" height="800" rx="176" fill="url(#tile)"/>'
        f'<g transform="translate({off},{off}) scale({scale})">{mark(WHITE)}</g>'
    )
    (OUT / "avatar.svg").write_text(svg_doc(800, 800, body_a, GRAD + tile))
    render_png(OUT / "avatar.svg", OUT / "avatar.png", 800)

    # 5. Light avatar: same soft gradient wash as the LinkedIn banner,
    #    navy-gradient pillars + cyan check (matches the light lockup).
    def radial(cid, cx, cy, r, color, opacity):
        return (
            f'<radialGradient id="{cid}" gradientUnits="userSpaceOnUse" '
            f'cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
            f"</radialGradient>"
        )

    light_defs = (
        '<linearGradient id="lbase" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#dfe9f7"/>'
        f'<stop offset=".62" stop-color="#eef3fa"/>'
        '<stop offset="1" stop-color="#eef3fa"/></linearGradient>'
        + radial("sky", 120, -40, 460, SKY, 0.50)
        + radial("navy", 700, -70, 560, NAVY, 0.55)
        + radial("blue", 440, -30, 400, BLUE, 0.38)
    )
    scale_l = 3.6
    off_l = (800 - 120 * scale_l) / 2
    body_l = (
        '<rect width="800" height="800" fill="url(#lbase)"/>'
        '<rect width="800" height="800" fill="url(#sky)"/>'
        '<rect width="800" height="800" fill="url(#navy)"/>'
        '<rect width="800" height="800" fill="url(#blue)"/>'
        f'<g transform="translate({off_l},{off_l + 20}) scale({scale_l})">'
        f'{mark("url(#pillar)")}</g>'
    )
    (OUT / "avatar-light.svg").write_text(svg_doc(800, 800, body_l, GRAD + PILLAR_GRAD + light_defs))
    render_png(OUT / "avatar-light.svg", OUT / "avatar-light.png", 800)

    print("Built:", ", ".join(p.name for p in sorted(OUT.iterdir()) if p.suffix in {".svg", ".png"}))


if __name__ == "__main__":
    main()
