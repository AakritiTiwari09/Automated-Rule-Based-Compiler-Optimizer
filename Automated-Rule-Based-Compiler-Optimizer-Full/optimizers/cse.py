class CommonSubexpressionElimination:
    name = "Common Subexpression Elimination"

    def optimize(self, instructions):
        result, applied = [], []
        expressions = {}
        for ins in instructions:
            typ = ins["type"]
            if typ == "binop":
                key = (ins["operator"], ins["arg1"], ins["arg2"])
                if key in expressions:
                    existing = expressions[key]
                    result.append({"type":"assign","result":ins["result"],"arg1":existing})
                    applied.append(f"{ins['arg1']} {ins['operator']} {ins['arg2']} reused from {existing}")
                else:
                    expressions[key] = ins["result"]
                    result.append(ins)
                # A new assignment invalidates expressions using that variable.
                result_var = ins["result"]
                expressions = {
                    k:v for k,v in expressions.items()
                    if result_var not in (k[1], k[2])
                }
                expressions[key] = ins["result"]
            elif typ == "assign":
                result_var = ins["result"]
                expressions = {
                    k:v for k,v in expressions.items()
                    if result_var not in (k[1], k[2])
                }
                result.append(ins)
            elif typ == "input":
                result_var = ins["result"]
                expressions = {
                    k:v for k,v in expressions.items()
                    if result_var not in (k[1], k[2])
                }
                result.append(ins)
            elif typ in ("label","goto","if_goto"):
                expressions.clear()
                result.append(ins)
            else:
                result.append(ins)
        return result, applied
