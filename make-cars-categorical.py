#!/usr/bin/env python3
"""Generate cars-categorical-*.csv test files from cars.csv.

Deterministic (no randomness) so regenerations stay stable. Run from this
directory:

    python3 make-cars-categorical.py
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cars.csv"

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

SPARSE_ROW_COUNT = 100
GRADES = (1, 2, 5, 9)
REGIONS = ("North", "south", "EAST")
EMPTYISH = ("", "none", "ok")


def read_cars() -> list[dict[str, str]]:
    with SOURCE.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path.name} ({len(rows)} rows)")


def every_nth(index: int, every: int, offset: int) -> bool:
    return (index - offset) % every == 0 and index >= offset


def make_nulls(rows: list[dict[str, str]]) -> None:
    out_rows: list[dict[str, str]] = []
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

        out_rows.append(
            {
                "Model": model,
                "MPG": row["MPG"],
                "Cylinders": cylinders,
                "Displacement": row["Displacement"],
                "Horsepower": row["Horsepower"],
                "Weight": row["Weight"],
                "Acceleration": row["Acceleration"],
                "Year": row["Year"],
                "Origin": row["Origin"],
                "Origin Label": origin_label,
                "Null Trap": null_trap,
            }
        )

    fieldnames = [
        "Model",
        "MPG",
        "Cylinders",
        "Displacement",
        "Horsepower",
        "Weight",
        "Acceleration",
        "Year",
        "Origin",
        "Origin Label",
        "Null Trap",
    ]
    write_csv(ROOT / "cars-categorical-nulls.csv", fieldnames, out_rows)


def make_wrap(rows: list[dict[str, str]]) -> None:
    out_rows: list[dict[str, str]] = []
    for i, row in enumerate(rows):
        # Seg01..Seg12 — inspectable wrap (e.g. Set2 has 8 colors).
        segment = f"Seg{(i % 12) + 1:02d}"
        # SegA..SegH — fits an 8-color discrete palette exactly.
        segment8 = f"Seg{chr(ord('A') + (i % 8))}"
        out_rows.append(
            {
                "Model": row["Model"],
                "MPG": row["MPG"],
                "Cylinders": row["Cylinders"],
                "Displacement": row["Displacement"],
                "Horsepower": row["Horsepower"],
                "Weight": row["Weight"],
                "Acceleration": row["Acceleration"],
                "Year": row["Year"],
                "Origin": row["Origin"],
                "Segment": segment,
                "Segment8": segment8,
            }
        )

    fieldnames = [
        "Model",
        "MPG",
        "Cylinders",
        "Displacement",
        "Horsepower",
        "Weight",
        "Acceleration",
        "Year",
        "Origin",
        "Segment",
        "Segment8",
    ]
    write_csv(ROOT / "cars-categorical-wrap.csv", fieldnames, out_rows)


def make_sparse(rows: list[dict[str, str]]) -> None:
    # First N rows with continuous MPG/Weight preserved for axes.
    subset = rows[:SPARSE_ROW_COUNT]
    out_rows: list[dict[str, str]] = []
    for i, row in enumerate(subset):
        grade = GRADES[i % len(GRADES)]
        out_rows.append(
            {
                "Model": row["Model"],
                "MPG": row["MPG"],
                "Weight": row["Weight"],
                "Grade": str(grade),
                "Grade Label": str(grade),
                "Fleet": "FleetA",
                "Region": REGIONS[i % len(REGIONS)],
                "Emptyish": EMPTYISH[i % len(EMPTYISH)],
            }
        )

    fieldnames = [
        "Model",
        "MPG",
        "Weight",
        "Grade",
        "Grade Label",
        "Fleet",
        "Region",
        "Emptyish",
    ]
    write_csv(ROOT / "cars-categorical-sparse.csv", fieldnames, out_rows)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source file: {SOURCE}")
    rows = read_cars()
    make_nulls(rows)
    make_wrap(rows)
    make_sparse(rows)


if __name__ == "__main__":
    main()
