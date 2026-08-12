#!/usr/bin/env python3
"""Generate cars-categorical.csv test file from cars.csv.

Deterministic (no randomness) so regenerations stay stable. Run from this
directory:

    python3 make-cars-categorical.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cars.csv"
OUTPUT = ROOT / "cars-categorical.csv"

ORIGIN_LABEL = {"1.0": "USA", "2.0": "Europe", "3.0": "Japan"}
# ~5% of 406 rows ≈ every 20th row, offset so columns don't null the same rows.
NULL_MODEL_EVERY = 20
NULL_MODEL_OFFSET = 3
NULL_CYL_EVERY = 20
NULL_CYL_OFFSET = 7
NULL_ORIGIN_LABEL_EVERY = 20
NULL_ORIGIN_LABEL_OFFSET = 11
NULL_TRAP_NULL_EVERY = 25
NULL_TRAP_NULL_OFFSET = 2
NULL_TRAP_LITERAL_NULL_EVERY = 40
NULL_TRAP_LITERAL_NULL_OFFSET = 5
NULL_TRAP_LITERAL_UNDEF_EVERY = 40
NULL_TRAP_LITERAL_UNDEF_OFFSET = 17

GRADES = (1, 2, 5, 9)
REGIONS = ("North", "south", "EAST")
EMPTYISH = ("", "none", "ok")

# Exactly 8 long strings — fits Set2-sized discrete colormaps; forces legend
# middle-ellipsis (~140px tick max width).
LONG_LABELS = (
    "North American Manufacturing Division Alpha",
    "Southwestern European Distribution Center Beta",
    "Pacific Rim Logistics and Supply Chain Gamma",
    "Central Plains Research Laboratory Delta",
    "Atlantic Coastal Engineering Station Epsilon",
    "Mountain West Quality Assurance Facility Zeta",
    "Great Lakes Production Operations Eta",
    "Gulf Coast Materials Testing Institute Theta",
)

# Plain decimal only (digits, '.', optional leading '-') so PS parses as float.
# Covers human-scale longs (grouped ,~f), tiny/huge magnitudes (.2g), pitfalls.
LONG_NUMBERS = (
    "30000000",
    "1234567890",
    "12345678901234.5",
    "0.0000001",
    "0.0000001234567890123456",
    "0.30000000000000004",
    "3.141592653589793",
    "2.718281828459045",
    "1.4142135623730951",
    "0.1",
    "0.01",
    "0.001",
    "0.000000000001",
    "1000000000000",
    "999",
    "1000",
    "999999",
    "1000000",
    "-30000000",
    "-0.0000001234",
    "0",
    "1",
    "-1",
    "0.9999999999999999",
    "1000000000.0000001",
    "0.000000000000001",
    "1000000000000000000",
    "5550000000000000",
    "1234567890123456",
    "100000000000",
)

# Exactly 8 long numeric codes — column header flags wizard categorical mark.
LONG_CODES = (
    "12345678901234.5",
    "30000000",
    "0.000000123456789",
    "5550000000000000",
    "1000000000000000000",
    "0.30000000000000004",
    "1234567890",
    "0.000000000000001",
)

# Headers ending in " (categorical)" are numeric columns to mark categorical
# in the PS creation wizard. String columns are categorical automatically.
FIELDNAMES = [
    "Model",
    "MPG",
    "Cylinders (categorical)",
    "Displacement",
    "Horsepower",
    "Weight",
    "Acceleration",
    "Year",
    "Origin (categorical)",
    "Origin Label",
    "Null Trap",
    "Segment",
    "Segment8",
    "Grade (categorical)",
    "Grade Label",
    "Fleet",
    "Region",
    "Emptyish",
    "Log Spaced",
    "Long Label",
    "Long Number",
    "Long Code (categorical)",
]


def read_cars() -> list[dict[str, str]]:
    with SOURCE.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path.name} ({len(rows)} rows)")


# Geometric series spanning 6 decades — evenly spaced on a log axis.
LOG_SPACED_MIN = 1e-3
LOG_SPACED_MAX = 1e3


def every_nth(index: int, every: int, offset: int) -> bool:
    return (index - offset) % every == 0 and index >= offset


def log_spaced(index: int, count: int) -> str:
    """Value i of count evenly spaced in log10 space from MIN to MAX."""
    if count <= 1:
        return format(LOG_SPACED_MIN, ".17g")
    t = index / (count - 1)
    value = 10 ** (
        math.log10(LOG_SPACED_MIN)
        + t * (math.log10(LOG_SPACED_MAX) - math.log10(LOG_SPACED_MIN))
    )
    return format(value, ".17g")


def make_categorical(rows: list[dict[str, str]]) -> None:
    out_rows: list[dict[str, str]] = []
    n = len(rows)
    for i, row in enumerate(rows):
        model = "" if every_nth(i, NULL_MODEL_EVERY, NULL_MODEL_OFFSET) else row["Model"]
        cylinders = "NaN" if every_nth(i, NULL_CYL_EVERY, NULL_CYL_OFFSET) else row["Cylinders"]
        origin_label = ORIGIN_LABEL.get(row["Origin"], "Unknown")
        if every_nth(i, NULL_ORIGIN_LABEL_EVERY, NULL_ORIGIN_LABEL_OFFSET):
            origin_label = ""

        # Mostly A/B/C by row; inject real nulls and literal trap strings.
        null_trap = ("A", "B", "C")[i % 3]
        if every_nth(i, NULL_TRAP_NULL_EVERY, NULL_TRAP_NULL_OFFSET):
            null_trap = ""
        elif every_nth(i, NULL_TRAP_LITERAL_NULL_EVERY, NULL_TRAP_LITERAL_NULL_OFFSET):
            null_trap = "null"
        elif every_nth(i, NULL_TRAP_LITERAL_UNDEF_EVERY, NULL_TRAP_LITERAL_UNDEF_OFFSET):
            null_trap = "undefined"

        # Seg01..Seg12 — inspectable wrap (e.g. Set2 has 8 colors).
        segment = f"Seg{(i % 12) + 1:02d}"
        # SegA..SegH — fits an 8-color discrete palette exactly.
        segment8 = f"Seg{chr(ord('A') + (i % 8))}"

        grade = GRADES[i % len(GRADES)]

        out_rows.append(
            {
                "Model": model,
                "MPG": row["MPG"],
                "Cylinders (categorical)": cylinders,
                "Displacement": row["Displacement"],
                "Horsepower": row["Horsepower"],
                "Weight": row["Weight"],
                "Acceleration": row["Acceleration"],
                "Year": row["Year"],
                "Origin (categorical)": row["Origin"],
                "Origin Label": origin_label,
                "Null Trap": null_trap,
                "Segment": segment,
                "Segment8": segment8,
                "Grade (categorical)": str(grade),
                "Grade Label": str(grade),
                "Fleet": "FleetA",
                "Region": REGIONS[i % len(REGIONS)],
                "Emptyish": EMPTYISH[i % len(EMPTYISH)],
                "Log Spaced": log_spaced(i, n),
                "Long Label": LONG_LABELS[i % len(LONG_LABELS)],
                "Long Number": LONG_NUMBERS[i % len(LONG_NUMBERS)],
                "Long Code (categorical)": LONG_CODES[i % len(LONG_CODES)],
            }
        )

    write_csv(OUTPUT, FIELDNAMES, out_rows)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source file: {SOURCE}")
    make_categorical(read_cars())


if __name__ == "__main__":
    main()
