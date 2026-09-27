#!/usr/bin/env python3
"""Convert stock Snapmaker U1 process line widths from mm to nozzle percentages.

Run from any directory. Existing percentage values and custom user presets are
left alone. Orca resolves the resulting values against each active tool's nozzle.
"""

import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


PROCESSES = Path(__file__).resolve().parents[1] / "resources/profiles/Snapmaker/process"
WIDTH_ENTRY = re.compile(r'("(?:line_width|[a-z_]+_line_width)"\s*:\s*")([^"]+)(")')
NAMED_NOZZLE = re.compile(r"\((0\.[0-9]+) nozzle\)$")
HIDDEN_NOZZLE = re.compile(r"nozzle_(0\.[0-9]+)")
COMMON_NOZZLE = re.compile(r"fdm_process_U1_(0\.[0-9]+)_common$")


def intended_nozzle(profile):
    name = profile["name"]
    match = NAMED_NOZZLE.search(name) or HIDDEN_NOZZLE.search(name) or COMMON_NOZZLE.fullmatch(name)
    # The unsuffixed U1 profiles and common base profiles target the 0.4 mm nozzle.
    return Decimal(match.group(1)) if match else Decimal("0.4")


def convert(text, nozzle):
    def replace(match):
        raw = match.group(2)
        if raw.endswith("%") or not raw:
            return match.group(0)
        try:
            width = Decimal(raw)
        except Exception as error:
            raise ValueError(f"Unexpected line width: {raw!r}") from error
        if width <= 0:
            return match.group(0)  # Zero retains Orca's automatic width behavior.
        percent = (width * 100 / nozzle).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{match.group(1)}{percent}%{match.group(3)}"

    return WIDTH_ENTRY.sub(replace, text)


def main():
    changed = 0
    for path in sorted(PROCESSES.glob("*.json")):
        if "U1" not in path.name:
            continue
        original = path.read_text(encoding="utf-8")
        profile = json.loads(original)
        if "Snapmaker U1" not in profile["name"] and not profile["name"].startswith("fdm_process_U1"):
            continue
        updated = convert(original, intended_nozzle(profile))
        if updated != original:
            json.loads(updated)
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"Updated {changed} U1 process profiles")


if __name__ == "__main__":
    main()
