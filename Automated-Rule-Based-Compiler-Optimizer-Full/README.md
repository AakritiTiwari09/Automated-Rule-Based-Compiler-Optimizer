# Automated Rule-Based Compiler Code Optimizer

Compiler Design Lab Project.

## Full pipeline

Source → Lexer → Recursive-Descent Parser → Three Address Code → Optimization Engine → TAC Interpreter → Output Verification → Metrics → Benchmark → Graphs

## Six required optimizations

1. Constant Folding
2. Constant Propagation
3. Algebraic Simplification
4. Common Subexpression Elimination
5. Dead Code Elimination
6. Strength Reduction

The engine repeats optimization passes until the TAC reaches a fixed point or the safety limit of 20 passes.

## Language

Supported:
- integer constants
- identifiers
- `+ - * /`
- parentheses
- assignments
- `print`
- `input`
- `if / else`
- `while`
- comparisons: `== != < > <= >=`

Example:

```text
input a;
x = a + 0;
y = x * 2;
print y;
```

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run command-line demo:

```bash
python main.py
```

Run GUI:

```bash
python -m gui.app
```

Generate the 100-program dataset:

```bash
python dataset/generate_dataset.py
```

Run benchmark:

```bash
python benchmark.py
```

Generate plots after benchmark:

```bash
python visualization.py
```

Run tests:

```bash
python -m pytest
```
