def is_constant(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False

def const_value(value):
    return int(value)

def variables_in_instruction(ins):
    out = set()
    typ = ins["type"]
    if typ == "assign":
        if not is_constant(ins["arg1"]): out.add(ins["arg1"])
    elif typ == "binop":
        if not is_constant(ins["arg1"]): out.add(ins["arg1"])
        if not is_constant(ins["arg2"]): out.add(ins["arg2"])
    elif typ == "print":
        if not is_constant(ins["arg1"]): out.add(ins["arg1"])
    elif typ == "if_goto":
        if not is_constant(ins["arg1"]): out.add(ins["arg1"])
        if not is_constant(ins["arg2"]): out.add(ins["arg2"])
    return out
