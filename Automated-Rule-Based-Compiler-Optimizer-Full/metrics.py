import time

ARITHMETIC = {"+", "-", "*", "/"}

def count_metrics(instructions, tac_formatter):
    text = "\n".join(tac_formatter(i) for i in instructions)
    instruction_count = len(instructions)
    operation_count = sum(
        1 for i in instructions
        if i.get("type") == "binop" and i.get("operator") in ARITHMETIC
    )
    temporaries = {
        i["result"] for i in instructions
        if i.get("result", "").startswith("t")
    }
    return {
        "instruction_count": instruction_count,
        "operation_count": operation_count,
        "temporary_count": len(temporaries),
        "code_size": len(text),
    }

def reduction(before, after):
    return 0.0 if before == 0 else (before - after) / before * 100.0

def execution_time(interpreter, instructions, inputs=None, repeats=5):
    values = []
    output = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = interpreter.execute(instructions, inputs)
        values.append(time.perf_counter() - start)
        output = result["output_text"]
    return sum(values) / len(values), output
