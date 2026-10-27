import json
import csv
from pathlib import Path
from compiler.pipeline import compile_source
from compiler.interpreter import TACInterpreter
from optimizers.engine import OptimizationEngine
from metrics import count_metrics, reduction

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
RESULTS = ROOT / "results"


def load_programs():
    programs = []
    for path in sorted(DATASET.glob("cat*/*.json")):
        with path.open("r", encoding="utf-8") as f:
            programs.append(json.load(f))
    return programs


def infer_inputs(program, category=None):
    # The supported input programs in this benchmark use one input variable, a.
    if "input a;" in program.get("source", ""):
        return [1, 2, 5, 10, 20]
    return [None] * 5


def pct_reduction(before, after):
    return round((before - after) * 100.0 / before, 2) if before else 0.0


def run():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    per_optimizer = {}
    category_totals = {}

    for p in load_programs():
        _, tac = compile_source(p["source"])
        original = tac.instructions
        optimized, info = OptimizationEngine().optimize(original)
        before = count_metrics(original, tac.format_instruction)
        after = count_metrics(optimized, tac.format_instruction)

        test_values = infer_inputs(p, p.get("category"))
        passed = 0
        for value in test_values:
            inputs = [] if value is None else [value]
            original_output = TACInterpreter().execute(original, inputs)["output_text"]
            optimized_output = TACInterpreter().execute(optimized, inputs)["output_text"]
            if original_output == optimized_output:
                passed += 1

        for name, count in info["fired"].items():
            stat = per_optimizer.setdefault(name, {"programs": 0, "changes": 0})
            if count:
                stat["programs"] += 1
                stat["changes"] += count

        category = p["category"]
        totals = category_totals.setdefault(category, {
            "programs": 0,
            "before": 0, "after": 0,
            "before_operations": 0, "after_operations": 0,
            "before_temporaries": 0, "after_temporaries": 0,
            "before_code_size": 0, "after_code_size": 0,
            "tests_passed": 0, "tests_total": 0,
        })
        totals["programs"] += 1
        for metric, key in [
            ("instruction_count", "instructions"),
            ("operation_count", "operations"),
            ("temporary_count", "temporaries"),
            ("code_size", "code_size"),
        ]:
            totals[f"before_{key}" if key != "instructions" else "before"] += before[metric]
            totals[f"after_{key}" if key != "instructions" else "after"] += after[metric]
        totals["tests_passed"] += passed
        totals["tests_total"] += len(test_values)

        rows.append({
            "id": p["id"],
            "category": category,
            "before_instructions": before["instruction_count"],
            "after_instructions": after["instruction_count"],
            "instruction_reduction_pct": pct_reduction(before["instruction_count"], after["instruction_count"]),
            "before_operations": before["operation_count"],
            "after_operations": after["operation_count"],
            "operation_reduction_pct": pct_reduction(before["operation_count"], after["operation_count"]),
            "before_temporaries": before["temporary_count"],
            "after_temporaries": after["temporary_count"],
            "temporary_reduction_pct": pct_reduction(before["temporary_count"], after["temporary_count"]),
            "before_code_size": before["code_size"],
            "after_code_size": after["code_size"],
            "code_size_reduction_pct": pct_reduction(before["code_size"], after["code_size"]),
            "passes": info["passes"],
            "tests_passed": passed,
            "tests_total": len(test_values),
        })

    if rows:
        with (RESULTS / "benchmark_results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def sum_field(field):
        return sum(float(r[field]) for r in rows)

    total_tests = sum_field("tests_total")
    total_passed = sum_field("tests_passed")
    # These are averages of per-program percentage changes, matching the
    # dashboard's "Avg ... Reduction" labels (rather than pooled totals).
    def average_pct(field):
        return round(sum(float(r[field]) for r in rows) / len(rows), 2) if rows else 0.0

    summary = {
        "programs": len(rows),
        "tests": int(total_tests),
        "passed": int(total_passed),
        "correctness": round(total_passed * 100.0 / total_tests, 2) if total_tests else 0.0,
        "instruction_reduction": average_pct("instruction_reduction_pct"),
        "operation_reduction": average_pct("operation_reduction_pct"),
        "temporary_reduction": average_pct("temporary_reduction_pct"),
        "code_size_reduction": average_pct("code_size_reduction_pct"),
        "per_optimizer": per_optimizer,
        "category_totals": category_totals,
    }
    with (RESULTS / "benchmark_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
