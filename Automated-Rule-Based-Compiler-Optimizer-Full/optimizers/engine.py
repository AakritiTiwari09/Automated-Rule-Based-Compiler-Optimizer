from .constant_folding import ConstantFolding
from .constant_propagation import ConstantPropagation
from .algebraic_simplification import AlgebraicSimplification
from .cse import CommonSubexpressionElimination
from .dead_code import DeadCodeElimination
from .strength_reduction import StrengthReduction

class OptimizationEngine:
    def __init__(self, enabled=None, max_passes=20):
        self.optimizers = [
            ConstantFolding(),
            ConstantPropagation(),
            AlgebraicSimplification(),
            CommonSubexpressionElimination(),
            DeadCodeElimination(),
            StrengthReduction(),
        ]
        self.enabled = set(enabled) if enabled else {o.name for o in self.optimizers}
        self.max_passes = max_passes

    def optimize(self, instructions):
        current = [dict(i) for i in instructions]
        all_logs = []
        pass_stats = []
        fired = {o.name: 0 for o in self.optimizers}

        for pass_no in range(1, self.max_passes + 1):
            before = self._serialize(current)
            pass_log = []
            for optimizer in self.optimizers:
                if optimizer.name not in self.enabled:
                    continue
                current, applied = optimizer.optimize(current)
                if applied:
                    fired[optimizer.name] += len(applied)
                    pass_log.append({
                        "optimizer": optimizer.name,
                        "changes": applied,
                        "count": len(applied)
                    })
            after = self._serialize(current)
            pass_stats.append({
                "pass": pass_no,
                "before_instructions": len(before),
                "after_instructions": len(after),
                "changes": sum(x["count"] for x in pass_log)
            })
            all_logs.extend(pass_log)
            if before == after:
                break

        return current, {
            "logs": all_logs,
            "pass_stats": pass_stats,
            "fired": fired,
            "passes": len(pass_stats),
            "converged": bool(pass_stats),
        }

    @staticmethod
    def _serialize(instructions):
        return tuple(tuple(sorted(i.items())) for i in instructions)
