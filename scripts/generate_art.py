#!/usr/bin/env python3
"""Render two interlinked dot-matrix rings in equilibrium. Requires Pillow.

Run: python3 scripts/generate_art.py
Recolor: --light-ink '#24292f' --dark-ink '#e6edf3'
Two equally sized rings share a continuous tumble. Dots flow in opposite
directions along their surfaces. No center marker or orbital guide is drawn.
"""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 168, 144
SCALE = 2
FRAMES = 200
TAU = math.tau


def geometry():
    # Equal toroidal surfaces in perpendicular planes form a Hopf link.
    return [
        (TAU * ring / 80, TAU * spoke / 8, side)
        for side in (-1, 1)
        for ring in range(80)
        for spoke in range(8)
    ]


def project(points, phase):
    # Perspective, tumbling silhouettes and depth-sized dots restore the
    # sculptural quality of the original trefoil. Every motion is periodic.
    yaw = phase + 0.45
    pitch = 0.58 + 0.30 * math.sin(phase)
    roll = -0.38 + 0.20 * math.sin(2 * phase)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    projected = []
    for u, v, side in points:
        angle = u + side * phase
        tube = 1.18 + 0.25 * math.cos(v)
        x = side * 0.72 + tube * math.cos(angle)
        y, z = tube * math.sin(angle), 0.25 * math.sin(v)
        if side == 1:
            y, z = z, y
        x, z = x * cy + z * sy, -x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        x, y = x * cr - y * sr, x * sr + y * cr
        perspective = 7 / (7 - z)
        depth = max(0, min(1, (z + 2.5) / 5))
        wave = (0.5 + 0.5 * math.cos(2 * angle - side * phase + v)) ** 4
        radius = (0.31 + 0.43 * depth + 0.10 * wave) * perspective
        light = max(0, min(1, 0.10 + 0.68 * depth + 0.22 * wave))
        projected.append((z, WIDTH / 2 + x * 26 * perspective,
                          HEIGHT / 2 + y * 26 * perspective, radius, light))
    return sorted(projected)


def palette(ink, theme):
    # Opaque dot shades, transparent negative space; no baked-in rectangle.
    faint = (170, 178, 188) if theme == "light" else (64, 74, 87)
    colors = [0, 0, 0]
    for level in range(1, 33):
        amount = (level - 1) / 31
        colors.extend(round(a + (b - a) * amount) for a, b in zip(faint, ink))
    return colors + [0] * (768 - len(colors))


def render(points, phase, colors):
    image = Image.new("P", (WIDTH * SCALE, HEIGHT * SCALE), 0)
    image.putpalette(colors)
    draw = ImageDraw.Draw(image)
    for _, x, y, radius, light in project(points, phase):
        box = tuple(round(n * SCALE) for n in (x - radius, y - radius, x + radius, y + radius))
        draw.ellipse(box, fill=1 + round(light * 31))
    image.info["transparency"] = 0
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--light-ink", default="#24292f")
    parser.add_argument("--dark-ink", default="#e6edf3")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    points = geometry()
    for theme, ink in (("light", args.light_ink), ("dark", args.dark_ink)):
        colors = palette(ImageColor.getrgb(ink), theme)
        frames = [render(points, TAU * frame / FRAMES, colors) for frame in range(FRAMES)]
        frames[0].save(args.output / f"equilibrium-{theme}.png", transparency=0)
        frames[0].save(
            args.output / f"equilibrium-{theme}.gif", save_all=True,
            append_images=frames[1:], duration=50, loop=0,
            transparency=0, background=0, disposal=2, optimize=False,
        )
        print(f"Generated {theme} equilibrium: {FRAMES} frames, {FRAMES * 50} ms")


if __name__ == "__main__":
    main()
