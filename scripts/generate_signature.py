#!/usr/bin/env python3
"""Render the profile signature. Requires Pillow: python3 -m pip install Pillow.

Recolor with --light-ink '#57606a' --dark-ink '#adbac7', then commit all four
generated assets. The seed keeps the motion identical across both themes.
"""

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
WIDTH, HEIGHT = 108, 72
DOT = 3
GLYPHS = (
    "10000 00000",
    "10000 00000",
    "10110 11111",
    "11001 00010",
    "10001 00100",
    "10001 01000",
    "11110 11111",
)
TARGETS = [
    (19 + column * 6, 16 + row * 6)
    for row, line in enumerate(GLYPHS)
    for column, cell in enumerate(line.replace(" ", "  "))
    if cell == "1"
]


def ease(value):
    """Smooth acceleration and deceleration without overshoot."""
    return value * value * (3 - 2 * value)


def choreography():
    rng = random.Random(17)
    scattered = [
        (rng.uniform(10, WIDTH - DOT - 10), rng.uniform(9, HEIGHT - DOT - 9))
        for _ in TARGETS
    ]
    delays = [rng.uniform(0, 0.18) for _ in TARGETS]
    frames = [(TARGETS, 3200)]
    for step in range(1, 29):
        progress = step / 28
        positions = []
        for target, destination, delay in zip(TARGETS, scattered, delays):
            amount = ease(max(0, min(1, (progress - delay) / (1 - delay))))
            positions.append(tuple(a + (b - a) * amount for a, b in zip(target, destination)))
        frames.append((positions, 50))
    frames.append((scattered, 250))
    for step in range(1, 33):
        progress = step / 32
        positions = []
        for target, origin, delay in zip(TARGETS, scattered, reversed(delays)):
            amount = ease(max(0, min(1, (progress - delay) / (1 - delay))))
            positions.append(tuple(a + (b - a) * amount for a, b in zip(origin, target)))
        frames.append((positions, 50))
    frames.append((TARGETS, 2200))
    return frames


def render(positions, color):
    image = Image.new("P", (WIDTH * SCALE, HEIGHT * SCALE), 0)
    image.putpalette([0, 0, 0, *color] + [0, 0, 0] * 254)
    draw = ImageDraw.Draw(image)
    for x, y in positions:
        x, y = math.floor(x * SCALE), math.floor(y * SCALE)
        draw.rectangle((x, y, x + DOT * SCALE - 1, y + DOT * SCALE - 1), fill=1)
    image.info["transparency"] = 0
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--light-ink", default="#57606a")
    parser.add_argument("--dark-ink", default="#adbac7")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    motion = choreography()
    for theme, ink in (("light", args.light_ink), ("dark", args.dark_ink)):
        color = ImageColor.getrgb(ink)
        frames = [render(positions, color) for positions, _ in motion]
        frames[0].save(args.output / f"signature-{theme}.png", transparency=0)
        frames[0].save(
            args.output / f"signature-{theme}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=[duration for _, duration in motion],
            loop=0,
            transparency=0,
            background=0,
            disposal=2,
            optimize=False,
        )
        print(f"Generated {theme} signature in {args.output}")


if __name__ == "__main__":
    main()
