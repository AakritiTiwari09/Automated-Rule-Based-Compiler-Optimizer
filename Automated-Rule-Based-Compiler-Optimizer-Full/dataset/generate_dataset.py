import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def write(category, idx, source, expected_outputs):
    path = ROOT / category / f"program_{idx:02d}.json"
    path.write_text(json.dumps({
        "id": f"{category}_{idx:02d}",
        "category": category,
        "source": source,
        "expected_outputs": expected_outputs
    }, indent=2), encoding="utf-8")

def main():
    # Five deterministic benchmark categories, 20 each.
    for i in range(1, 21):
        a, b = i + 2, i + 5
        source = f"x = {a} * {b};\ny = x + {i};\nprint y;"
        write("cat1_constant", i, source, [str(a*b+i)])

        source = f"input a;\nx = a + 0;\ny = x * 1;\nprint y;"
        write("cat2_algebraic", i, source, [str(i)])

        source = f"input a;\nt1 = a + {i};\nt2 = t1 * 2;\nx = 999;\nprint t2;"
        write("cat3_dead_code", i, source, [str((i+i)*2)])

        source = f"input a;\nt1 = a + {i};\nt2 = a * 2;\nt3 = a + {i};\nprint t3;"
        write("cat4_cse", i, source, [str(i+i)])

        n = i % 10 + 3
        source = f"i = 0;\ns = 0;\nwhile (i < {n}) {{\n  x = i * 2;\n  s = s + x;\n  i = i + 1;\n}}\nprint s;"
        expected = n * (n - 1)
        write("cat5_loops", i, source, [str(expected)])

if __name__ == "__main__":
    main()
