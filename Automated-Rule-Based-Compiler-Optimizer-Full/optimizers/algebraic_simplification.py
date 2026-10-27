class AlgebraicSimplification:
    name = "Algebraic Simplification"

    RULES = {
        ("+", "0", "right"): "left",
        ("-", "0", "right"): "left",
        ("*", "1", "right"): "left",
        ("/", "1", "right"): "left",
        ("+", "0", "left"): "right",
        ("*", "0", "left"): "zero",
        ("*", "0", "right"): "zero",
        ("*", "1", "left"): "right",
    }

    def optimize(self, instructions):
        result, applied = [], []
        for ins in instructions:
            if ins["type"] != "binop":
                result.append(ins); continue
            a, b, op = ins["arg1"], ins["arg2"], ins["operator"]
            replacement = None
            if op in ("+", "-", "*", "/"):
                if op in ("+", "-", "*", "/") and b == "0" and op in ("+", "-"):
                    replacement = a
                elif op in ("*", "/") and b == "1":
                    replacement = a
                elif op == "+" and a == "0":
                    replacement = b
                elif op == "*" and a == "1":
                    replacement = b
                elif op == "*" and (a == "0" or b == "0"):
                    replacement = "0"
            if replacement is not None:
                result.append({"type":"assign","result":ins["result"],"arg1":replacement})
                applied.append(f"{a} {op} {b} → {replacement}")
            else:
                result.append(ins)
        return result, applied
