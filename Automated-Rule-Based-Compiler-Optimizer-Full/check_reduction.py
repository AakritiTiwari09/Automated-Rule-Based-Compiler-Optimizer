
import csv

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "results" / "benchmark_results.csv"

with CSV_FILE.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    print("No benchmark results found.")
    raise SystemExit

# Method 1: Average individual program reductions
individual_reductions = [
    float(row["instruction_reduction_pct"])
    for row in rows
]

average_individual = (
    sum(individual_reductions) / len(individual_reductions)
)

# Method 2: Reduction based on total instruction counts
total_before = sum(
    int(row["before_instructions"])
    for row in rows
)

total_after = sum(
    int(row["after_instructions"])
    for row in rows
)

pooled_reduction = (
    (total_before - total_after) / total_before * 100
    if total_before else 0
)

print("Total Programs:", len(rows))
print("Total Instructions Before:", total_before)
print("Total Instructions After:", total_after)

print(
    f"\nAverage Individual Reduction: "
    f"{average_individual:.2f}%"
)

print(
    f"Pooled Instruction Reduction: "
    f"{pooled_reduction:.2f}%"
)
