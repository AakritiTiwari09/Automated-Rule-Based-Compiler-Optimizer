from .utils import is_constant

class ConstantPropagation:
    name = "Constant Propagation"

    def optimize(self, instructions):
        env, result, applied = {}, [], []
        for ins in instructions:
            typ = ins["type"]
            if typ == "assign":
                src = ins["arg1"]
                if src in env:
                    src = env[src]
                    applied.append(f"{ins['result']} = {ins['arg1']} → {src}")
                result.append({"type":"assign","result":ins["result"],"arg1":src})
                if is_constant(src):
                    env[ins["result"]] = src
                else:
                    env.pop(ins["result"], None)
            elif typ == "binop":
                a, b = ins["arg1"], ins["arg2"]
                if a in env:
                    applied.append(f"{a} → {env[a]}")
                    a = env[a]
                if b in env:
                    applied.append(f"{b} → {env[b]}")
                    b = env[b]
                result.append({**ins, "arg1":a, "arg2":b})
                env.pop(ins["result"], None)
            elif typ == "input":
                env.pop(ins["result"], None)
                result.append(ins)
            elif typ in ("print","if_goto"):
                new = dict(ins)
                for k in ("arg1","arg2"):
                    if k in new and new[k] in env:
                        new[k] = env[new[k]]
                result.append(new)
            elif typ in ("label","goto"):
                result.append(ins)
                # Conservative across control-flow boundaries.
                env.clear()
            else:
                result.append(ins)
        return result, applied
