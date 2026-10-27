class TAC:
    def __init__(self):
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0

    def new_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit_assign(self, result, value):
        self.instructions.append({"type": "assign", "result": result, "arg1": str(value)})

    def emit_binop(self, result, left, operator, right):
        self.instructions.append({
            "type": "binop", "result": result, "arg1": str(left),
            "operator": operator, "arg2": str(right)
        })

    def emit_print(self, value):
        self.instructions.append({"type": "print", "arg1": str(value)})

    def emit_input(self, result):
        self.instructions.append({"type": "input", "result": result})

    def emit_label(self, label):
        self.instructions.append({"type": "label", "label": label})

    def emit_goto(self, label):
        self.instructions.append({"type": "goto", "label": label})

    def emit_if_goto(self, left, operator, right, label):
        self.instructions.append({
            "type": "if_goto", "arg1": str(left), "operator": operator,
            "arg2": str(right), "label": label
        })

    def format_instruction(self, ins):
        typ = ins["type"]
        if typ == "assign":
            return f'{ins["result"]} = {ins["arg1"]}'
        if typ == "binop":
            return f'{ins["result"]} = {ins["arg1"]} {ins["operator"]} {ins["arg2"]}'
        if typ == "print":
            return f'print {ins["arg1"]}'
        if typ == "input":
            return f'input {ins["result"]}'
        if typ == "label":
            return f'{ins["label"]}:'
        if typ == "goto":
            return f'goto {ins["label"]}'
        if typ == "if_goto":
            return f'if {ins["arg1"]} {ins["operator"]} {ins["arg2"]} goto {ins["label"]}'
        return str(ins)

    def to_text(self, instructions=None):
        instructions = self.instructions if instructions is None else instructions
        return "\n".join(self.format_instruction(i) for i in instructions)
