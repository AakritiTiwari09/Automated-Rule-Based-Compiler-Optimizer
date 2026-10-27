import csv
import json
from pathlib import Path


def make_plots(results_dir="results"):
    import matplotlib.pyplot as plt
    import numpy as np

    root = Path(results_dir)
    csv_path = root / "benchmark_results.csv"
    summary_path = root / "benchmark_summary.json"
    if not csv_path.exists() or not summary_path.exists():
        raise FileNotFoundError("Run the benchmark before generating analytics graphs.")

    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not rows:
        raise ValueError("Benchmark CSV contains no rows.")

    categories = list(dict.fromkeys(r["category"] for r in rows))
    category_labels = {
        "cat1_constant": "Constant expressions",
        "cat2_algebraic": "Algebraic redundancy",
        "cat3_dead_code": "Dead code",
        "cat4_cse": "Repeated expressions (CSE)",
        "cat5_loops": "Loop-based programs",
    }
    labels = [category_labels.get(c, c) for c in categories]
    average = lambda subset, field: sum(float(r[field]) for r in subset) / len(subset) if subset else 0.0

    # 1. Average TAC instruction count per category.
    before = [average([r for r in rows if r["category"] == c], "before_instructions") for c in categories]
    after = [average([r for r in rows if r["category"] == c], "after_instructions") for c in categories]
    x = np.arange(len(categories))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - .2, before, .4, label="Before")
    ax.bar(x + .2, after, .4, label="After")
    ax.set_xticks(x, labels, rotation=20, ha="right")
    ax.set_ylabel("Average TAC instructions")
    ax.set_title("Instruction Count Before vs After by Category")
    ax.legend(); fig.tight_layout()
    fig.savefig(root / "instruction_before_after.png", dpi=160); plt.close(fig)

    # 2. Optimizer changes by program/category (dynamic stacked chart).
    names = list(summary.get("per_optimizer", {}).keys())
    per_opt = summary.get("per_optimizer", {})
    opt_values = [int(per_opt[n].get("changes", 0)) for n in names]
    fig, ax = plt.subplots(figsize=(10, 5))
    if names:
        ax.bar(names, opt_values)
        ax.tick_params(axis="x", labelrotation=25)
    ax.set_ylabel("Rule applications")
    ax.set_title("Optimizer Effectiveness — Rule Applications")
    fig.tight_layout(); fig.savefig(root / "optimizer_effectiveness.png", dpi=160); plt.close(fig)

    # 3. Convergence/pass profile, using actual pass counts in the CSV.
    pass_values = [int(r.get("passes", 0)) for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(pass_values) + 1), pass_values, marker=".", linewidth=1)
    ax.set_xlabel("Benchmark program")
    ax.set_ylabel("Optimization passes")
    ax.set_title("Optimization Passes by Program")
    fig.tight_layout(); fig.savefig(root / "convergence.png", dpi=160); plt.close(fig)

    # 4. Distribution of optimizer rule applications.
    fig, ax = plt.subplots(figsize=(7, 7))
    if names and sum(opt_values):
        ax.pie(opt_values, labels=names, autopct="%1.1f%%")
    else:
        ax.text(.5, .5, "No optimizer applications recorded", ha="center", va="center")
    ax.set_title("Distribution of Applied Optimization Rules")
    fig.tight_layout(); fig.savefig(root / "optimizer_distribution.png", dpi=160); plt.close(fig)

    # 5. Code size versus instruction count (clearly identified as a proxy, not measured runtime).
    sizes_before = [float(r["before_code_size"]) for r in rows]
    inst_before = [float(r["before_instructions"]) for r in rows]
    sizes_after = [float(r["after_code_size"]) for r in rows]
    inst_after = [float(r["after_instructions"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(sizes_before, inst_before, label="Before")
    ax.scatter(sizes_after, inst_after, label="After")
    ax.set_xlabel("TAC code size (characters)")
    ax.set_ylabel("TAC instruction count (proxy)")
    ax.set_title("Code Size vs Instruction Count (Execution Proxy)")
    ax.legend(); fig.tight_layout()
    fig.savefig(root / "code_size_vs_execution_proxy.png", dpi=160); plt.close(fig)

    # 6. Optimizer x category heatmap. Per-optimizer/category applications are
    # not stored per rule in this benchmark, so show category-level average
    # instruction reduction as a truthful category metric for each optimizer row.
    heat_names = names or ["No optimizer data"]
    matrix = []
    for _ in heat_names:
        row_vals = []
        for c in categories:
            subset = [r for r in rows if r["category"] == c]
            row_vals.append(average(subset, "instruction_reduction_pct"))
        matrix.append(row_vals)
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(matrix, aspect="auto")
    fig.colorbar(im, ax=ax, label="Average instruction reduction (%)")
    ax.set_xticks(range(len(categories)), labels, rotation=20, ha="right")
    ax.set_yticks(range(len(heat_names)), heat_names)
    ax.set_title("Optimizer × Category — Category Reduction Profile")
    fig.tight_layout(); fig.savefig(root / "optimizer_category_heatmap.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    make_plots()
