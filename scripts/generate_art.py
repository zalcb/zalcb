#!/usr/bin/env python3
"""Render a rotating dot-matrix trefoil. Requires Pillow.

Run: python3 scripts/generate_art.py
Recolor: --light-ink '#24292f' --dark-ink '#e6edf3'
All motion is periodic, so the animation loops without a pause or reset.
"""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 168, 144
SCALE = 2
FRAMES = 160
TAU = math.tau


def center(u):
    radius = 2 + 0.65 * math.cos(3 * u)
    return radius * math.cos(2 * u), radius * math.sin(2 * u), math.sin(3 * u)


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v)


def geometry():
    points = []
    for ring in range(112):
        u = TAU * ring / 112
        c = center(u)
        before, after = center(u - 0.001), center(u + 0.001)
        tangent = normalize(tuple(b - a for a, b in zip(before, after)))
        normal = normalize((-tangent[1], tangent[0], 0))
        tx, ty, tz = tangent
        nx, ny, nz = normal
        binormal = (ty * nz - tz * ny, tz * nx - tx * nz, tx * ny - ty * nx)
        for spoke in range(8):
            v = TAU * spoke / 8
            point = tuple(
                axis + 0.25 * (math.cos(v) * n + math.sin(v) * b)
                for axis, n, b in zip(c, normal, binormal)
            )
            points.append((*point, u, v))
    return points


def project(points, phase):
    # Full rotation plus a gentle rocking motion; both return exactly at 2π.
    yaw = phase
    pitch = 0.62 + 0.28 * math.sin(phase)
    roll = -0.25 + 0.15 * math.sin(2 * phase)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    projected = []
    for x, y, z, u, v in points:
        x, z = x * cy + z * sy, -x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        x, y = x * cr - y * sr, x * sr + y * cr
        perspective = 8 / (8 - z)
        depth = max(0, min(1, (z + 3) / 6))
        wave = (0.5 + 0.5 * math.cos(2 * u - 2 * phase + v * 0.4)) ** 4
        light = max(0, min(1, 0.12 + 0.68 * depth + 0.20 * wave))
        radius = (0.36 + 0.44 * depth + 0.12 * wave) * perspective
        projected.append((z, WIDTH / 2 + x * 21 * perspective,
                          HEIGHT / 2 + y * 21 * perspective, radius, light))
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
        frames[0].save(args.output / f"trefoil-{theme}.png", transparency=0)
        frames[0].save(
            args.output / f"trefoil-{theme}.gif", save_all=True,
            append_images=frames[1:], duration=50, loop=0,
            transparency=0, background=0, disposal=2, optimize=False,
        )
        print(f"Generated {theme} trefoil: {FRAMES} frames, {FRAMES * 50} ms")


if __name__ == "__main__":
    main()
