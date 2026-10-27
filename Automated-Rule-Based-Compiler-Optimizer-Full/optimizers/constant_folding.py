from .utils import is_constant

class ConstantFolding:
    name = "Constant Folding"

    def optimize(self, instructions):
        result, applied = [], []
        for ins in instructions:
            if ins["type"] == "binop" and is_constant(ins["arg1"]) and is_constant(ins["arg2"]):
                a, b, op = int(ins["arg1"]), int(ins["arg2"]), ins["operator"]
                if op == "/" and b == 0:
                    result.append(ins); continue
                value = {"+": a+b, "-": a-b, "*": a*b, "/": a//b}.get(op)
                if value is not None:
                    result.append({"type":"assign","result":ins["result"],"arg1":str(value)})
                    applied.append(f"{ins['arg1']} {op} {ins['arg2']} → {value}")
                    continue
            result.append(ins)
        return result, applied
