from .utils import variables_in_instruction

class DeadCodeElimination:
    name = "Dead Code Elimination"

    def optimize(self, instructions):
        live = set()
        removed = []
        kept = list(instructions)
        removed_set = set()

        for idx in range(len(instructions) - 1, -1, -1):
            ins = instructions[idx]
            typ = ins["type"]

            if typ in ("print", "input", "goto", "if_goto", "label"):
                live.update(variables_in_instruction(ins))
                continue

            if typ in ("assign", "binop"):
                target = ins["result"]
                # Named program variables are conservatively kept because their
                # assignments can be observable/used by future control flow.
                if target.startswith("t") and target not in live:
                    removed_set.add(idx)
                    removed.append(ins)
                else:
                    live.discard(target)
                    live.update(variables_in_instruction(ins))

        optimized = [ins for i, ins in enumerate(kept) if i not in removed_set]
        log = [f"Removed dead instruction: {self._fmt(ins)}" for ins in reversed(removed)]
        return optimized, log

    @staticmethod
    def _fmt(ins):
        if ins["type"] == "assign":
            return f'{ins["result"]} = {ins["arg1"]}'
        if ins["type"] == "binop":
            return f'{ins["result"]} = {ins["arg1"]} {ins["operator"]} {ins["arg2"]}'
        return str(ins)
