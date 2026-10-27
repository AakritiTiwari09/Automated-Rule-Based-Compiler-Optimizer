from compiler.pipeline import compile_source
from compiler.interpreter import TACInterpreter
from optimizers.engine import OptimizationEngine
from metrics import count_metrics, reduction

SOURCE = """x = 10 * 20;
y = x + 5;
z = y * 1;
print z;"""

def main():
    _, tac = compile_source(SOURCE)
    optimized, info = OptimizationEngine().optimize(tac.instructions)

    print("SOURCE\n------")
    print(SOURCE)
    print("\nORIGINAL TAC\n------------")
    print(tac.to_text())
    print("\nOPTIMIZED TAC\n-------------")
    print(tac.to_text(optimized))

    original = TACInterpreter().execute(tac.instructions)
    after = TACInterpreter().execute(optimized)

    b = count_metrics(tac.instructions, tac.format_instruction)
    a = count_metrics(optimized, tac.format_instruction)

    print("\nOPTIMIZATIONS")
    print("-------------")
    for item in info["logs"]:
        print("✓", item["optimizer"])
        for change in item["changes"][:8]:
            print("  ", change)

    print("\nMETRICS")
    print("-------")
    for key in ("instruction_count","operation_count","temporary_count","code_size"):
        print(f"{key}: {b[key]} -> {a[key]} ({reduction(b[key],a[key]):.1f}% reduction)")

    print("\nVERIFICATION")
    print("------------")
    print("Original output :", original["output_text"])
    print("Optimized output:", after["output_text"])
    print("VERDICT:", "PASS" if original["output_text"] == after["output_text"] else "FAIL")
    print("Optimization passes:", info["passes"])

if __name__ == "__main__":
    main()
