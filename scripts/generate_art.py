#!/usr/bin/env python3
"""Render a dot-matrix study of dynamic equilibrium. Requires Pillow.

Run: python3 scripts/generate_art.py
Recolor: --light-ink '#24292f' --dark-ink '#e6edf3'
Two equal forms orbit a fixed center. Every moving point has an opposite
partner, preserving balance throughout a periodic, seamless animation.
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
    points = []
    # Hollow, equally weighted shells, each with the same latitude lattice.
    for latitude in range(1, 16):
        v = math.pi * latitude / 16
        count = max(6, round(36 * math.sin(v)))
        for longitude in range(count):
            u = TAU * longitude / count
            x = 1.75 + 0.78 * math.sin(v) * math.cos(u)
            y = 0.78 * math.sin(v) * math.sin(u)
            z = 0.78 * math.cos(v)
            points.extend(((x, y, z, "shell"), (-x, -y, -z, "shell")))
    # Shared orbital track and a sparse axle make the counterbalance visible.
    for index in range(96):
        u = TAU * index / 96
        points.append((1.75 * math.cos(u), 1.75 * math.sin(u), 0, "orbit"))
    for index in range(1, 13):
        x = index * 0.072
        points.extend(((x, 0, 0, "axle"), (-x, 0, 0, "axle")))
    return points


def project(points, phase):
    # Orthographic projection preserves the exact visual midpoint. The whole
    # system gently tilts while the equally sized forms exchange positions.
    pitch = 0.68 + 0.18 * math.sin(phase)
    roll = -0.2 + 0.12 * math.sin(2 * phase)
    co, so = math.cos(phase), math.sin(phase)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    projected = []
    for x, y, z, kind in points:
        x, y = x * co - y * so, x * so + y * co
        y, z = y * cp - z * sp, y * sp + z * cp
        x, y = x * cr - y * sr, x * sr + y * cr
        depth = max(0, min(1, (z + 2.5) / 5))
        if kind == "shell":
            radius = 0.34 + 0.50 * depth
            light = 0.12 + 0.85 * depth
        elif kind == "orbit":
            radius, light = 0.36, 0.08 + 0.16 * depth
        else:
            radius, light = 0.32, 0.3
        projected.append((z, WIDTH / 2 + x * 24,
                          HEIGHT / 2 + y * 24, radius, light))
    projected.append((3, WIDTH / 2, HEIGHT / 2, 1.35, 0.95))
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
