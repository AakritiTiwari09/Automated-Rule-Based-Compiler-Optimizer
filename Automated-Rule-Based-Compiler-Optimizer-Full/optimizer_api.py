
from copy import deepcopy

from optimizers.engine import OptimizationEngine
from compiler.interpreter import TACInterpreter
from compiler.lexer import Lexer
from compiler.parser import Parser


class OptimizerAPIError(Exception):
    """Raised when source compilation or optimization fails."""
    pass


def optimize_source(source, inputs=None, enabled=None, max_passes=20):
    """
    Compile and optimize source code written in the project's custom language.

    Args:
        source: Source code as a string.
        inputs: Values supplied to input statements, if any.
        enabled: Optional set/list of optimizer names to enable.
        max_passes: Maximum number of optimization passes.

    Returns:
        Dictionary containing original TAC, optimized TAC,
        optimization statistics, and equivalence-test results.
    """

    if not isinstance(source, str) or not source.strip():
        raise OptimizerAPIError("Source code cannot be empty.")

    try:
        # 1. Convert source code into tokens.
        tokens = Lexer(source).tokenize()

        # 2. Parse tokens and generate TAC.
        tac = Parser(tokens).parse()

        # 3. Preserve original TAC for testing.
        original_instructions = deepcopy(tac.instructions)

        # 4. Run the optimization engine.
        engine = OptimizationEngine(
            enabled=enabled,
            max_passes=max_passes
        )

        optimized_instructions, optimization_report = engine.optimize(
            original_instructions
        )

        # 5. Execute original and optimized TAC independently.
        original_interpreter = TACInterpreter()
        optimized_interpreter = TACInterpreter()

        original_result = original_interpreter.execute(
            original_instructions,
            inputs=inputs
        )

        optimized_result = optimized_interpreter.execute(
            optimized_instructions,
            inputs=inputs
        )

        # 6. Identify compiler-generated temporary variables.
        # The TAC generator creates temporaries named t1, t2, t3, ...
        temporary_variables = {
            f"t{i}"
            for i in range(1, tac.temp_counter + 1)
        }

        # 7. Compare source-level variables only.
        original_variables = {
            name: value
            for name, value in original_result["variables"].items()
            if name not in temporary_variables
        }

        optimized_variables = {
            name: value
            for name, value in optimized_result["variables"].items()
            if name not in temporary_variables
        }

        # 8. Compare observable outputs and source-level state.
        equivalent = (
            original_result["output"] == optimized_result["output"]
            and original_variables == optimized_variables
        )

        # 9. Format TAC for display.
        original_text = tac.to_text(original_instructions)
        optimized_text = tac.to_text(optimized_instructions)

        before_count = len(original_instructions)
        after_count = len(optimized_instructions)

        reduction = (
            ((before_count - after_count) / before_count) * 100
            if before_count
            else 0.0
        )

        # 10. Return the optimization report.
        return {
            "original_tac": original_text,
            "optimized_tac": optimized_text,

            "original_instructions": original_instructions,
            "optimized_instructions": optimized_instructions,

            "optimization_report": optimization_report,

            "instructions_before": before_count,
            "instructions_after": after_count,
            "instruction_reduction_percent": round(reduction, 2),

            "equivalent": equivalent,

            "original_output": original_result["output_text"],
            "optimized_output": optimized_result["output_text"],

            "verification": (
                "PASSED" if equivalent else "FAILED"
            ),
        }

    except Exception as exc:
        raise OptimizerAPIError(str(exc)) from exc
