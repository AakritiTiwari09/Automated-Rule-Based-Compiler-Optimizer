class StrengthReduction:
    name = "Strength Reduction"

    def optimize(self, instructions):
        result, applied = [], []
        for ins in instructions:
            if ins["type"] == "binop" and ins["operator"] == "*":
                a, b = ins["arg1"], ins["arg2"]
                if b == "2":
                    result.append({
                        "type": "binop", "result": ins["result"],
                        "arg1": a, "operator": "+", "arg2": a
                    })
                    applied.append(f"{a} * 2 → {a} + {a}")
                    continue
                if a == "2":
                    result.append({
                        "type": "binop", "result": ins["result"],
                        "arg1": b, "operator": "+", "arg2": b
                    })
                    applied.append(f"2 * {b} → {b} + {b}")
                    continue
            result.append(ins)
        return result, applied
