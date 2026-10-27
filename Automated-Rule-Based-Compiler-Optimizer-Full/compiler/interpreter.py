class InterpreterError(Exception):
    pass

class TACInterpreter:
    def __init__(self):
        self.variables = {}
        self.output = []
        self.inputs = []
        self.input_index = 0

    def reset(self, inputs=None):
        self.variables.clear()
        self.output.clear()
        self.inputs = list(inputs or [])
        self.input_index = 0

    def _value(self, operand):
        if operand is None:
            raise InterpreterError("Missing operand.")
        try:
            return int(operand)
        except (ValueError, TypeError):
            if operand not in self.variables:
                raise InterpreterError(f"Undefined variable: {operand}")
            return self.variables[operand]

    def _calculate(self, left, op, right):
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/":
            if right == 0: raise InterpreterError("Division by zero.")
            return left // right
        raise InterpreterError(f"Unsupported operator: {op}")

    def _compare(self, left, op, right):
        return {
            "==": left == right, "!=": left != right,
            "<": left < right, ">": left > right,
            "<=": left <= right, ">=": left >= right
        }[op]

    def execute(self, instructions, inputs=None):
        self.reset(inputs)
        labels = {i["label"]: idx for idx, i in enumerate(instructions) if i["type"] == "label"}
        pc, steps = 0, 0
        max_steps = 1_000_000

        while pc < len(instructions):
            steps += 1
            if steps > max_steps:
                raise InterpreterError("Execution limit exceeded; possible infinite loop.")

            ins = instructions[pc]
            typ = ins["type"]

            if typ == "assign":
                self.variables[ins["result"]] = self._value(ins["arg1"])
                pc += 1
            elif typ == "binop":
                self.variables[ins["result"]] = self._calculate(
                    self._value(ins["arg1"]), ins["operator"], self._value(ins["arg2"])
                )
                pc += 1
            elif typ == "print":
                self.output.append(str(self._value(ins["arg1"])))
                pc += 1
            elif typ == "input":
                if self.input_index >= len(self.inputs):
                    raise InterpreterError(f"Input required for variable {ins['result']}.")
                self.variables[ins["result"]] = int(self.inputs[self.input_index])
                self.input_index += 1
                pc += 1
            elif typ == "label":
                pc += 1
            elif typ == "goto":
                pc = labels[ins["label"]]
            elif typ == "if_goto":
                if self._compare(self._value(ins["arg1"]), ins["operator"], self._value(ins["arg2"])):
                    pc = labels[ins["label"]]
                else:
                    pc += 1
            else:
                raise InterpreterError(f"Unsupported TAC instruction: {typ}")

        return {"variables": dict(self.variables), "output": list(self.output),
                "output_text": "\n".join(self.output)}
