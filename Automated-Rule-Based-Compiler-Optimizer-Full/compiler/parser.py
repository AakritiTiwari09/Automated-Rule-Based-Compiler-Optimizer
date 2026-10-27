from .tac import TAC

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.tac = TAC()

    def current(self): return self.tokens[self.pos]
    def advance(self):
        t = self.current(); self.pos += 1; return t
    def expect(self, typ):
        t = self.current()
        if t.type != typ:
            raise ParserError(f"Expected {typ}, found {t.type} ('{t.value}') at line {t.line}, column {t.column}")
        return self.advance()

    def parse(self):
        while self.current().type != "EOF":
            self.statement()
        return self.tac

    def statement(self):
        typ = self.current().type
        if typ == "IDENTIFIER": self.assignment()
        elif typ == "PRINT": self.print_statement()
        elif typ == "INPUT": self.input_statement()
        elif typ == "WHILE": self.while_statement()
        elif typ == "IF": self.if_statement()
        else:
            t = self.current()
            raise ParserError(f"Unexpected token '{t.value}' at line {t.line}, column {t.column}")

    def block(self):
        self.expect("LBRACE")
        while self.current().type not in ("RBRACE", "EOF"):
            self.statement()
        self.expect("RBRACE")

    def assignment(self):
        name = self.expect("IDENTIFIER").value
        self.expect("ASSIGN")
        value = self.expression()
        self.expect("SEMICOLON")
        self.tac.emit_assign(name, value)

    def print_statement(self):
        self.expect("PRINT")
        value = self.expression()
        self.expect("SEMICOLON")
        self.tac.emit_print(value)

    def input_statement(self):
        self.expect("INPUT")
        name = self.expect("IDENTIFIER").value
        self.expect("SEMICOLON")
        self.tac.emit_input(name)

    def while_statement(self):
        self.expect("WHILE")
        left, op, right = self.condition()
        start = self.tac.new_label()
        end = self.tac.new_label()
        # Re-emit condition inside the loop structure.
        self.tac.emit_label(start)
        self.tac.emit_if_goto(left, self.negate(op), right, end)
        self.block()
        self.tac.emit_goto(start)
        self.tac.emit_label(end)

    def if_statement(self):
        self.expect("IF")
        left, op, right = self.condition()
        else_label = self.tac.new_label()
        end_label = self.tac.new_label()
        self.tac.emit_if_goto(left, self.negate(op), right, else_label)
        self.block()
        self.tac.emit_goto(end_label)
        self.expect("ELSE")
        self.tac.emit_label(else_label)
        self.block()
        self.tac.emit_label(end_label)

    def condition(self):
        self.expect("LPAREN")
        left = self.expression()
        token = self.current()
        if token.type not in ("EQ", "NE", "LT", "GT", "LE", "GE"):
            raise ParserError("Expected comparison operator in condition.")
        op = self.advance().value
        right = self.expression()
        self.expect("RPAREN")
        return left, op, right

    @staticmethod
    def negate(op):
        return {"==": "!=", "!=": "==", "<": ">=", ">": "<=", "<=": ">", ">=": "<"}[op]

    def expression(self):
        left = self.term()
        while self.current().type in ("PLUS", "MINUS"):
            op = self.advance().value
            right = self.term()
            temp = self.tac.new_temp()
            self.tac.emit_binop(temp, left, op, right)
            left = temp
        return left

    def term(self):
        left = self.factor()
        while self.current().type in ("STAR", "SLASH"):
            op = self.advance().value
            right = self.factor()
            temp = self.tac.new_temp()
            self.tac.emit_binop(temp, left, op, right)
            left = temp
        return left

    def factor(self):
        t = self.current()
        if t.type == "NUMBER":
            self.advance(); return t.value
        if t.type == "IDENTIFIER":
            self.advance(); return t.value
        if t.type == "LPAREN":
            self.advance()
            value = self.expression()
            self.expect("RPAREN")
            return value
        raise ParserError(f"Expected number, identifier, or '('; found '{t.value}'")
