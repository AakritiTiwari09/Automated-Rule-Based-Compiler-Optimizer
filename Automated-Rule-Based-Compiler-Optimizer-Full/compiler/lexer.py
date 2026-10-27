from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

class LexerError(Exception):
    pass

class Lexer:
    KEYWORDS = {"print", "input", "if", "else", "while"}

    SINGLE = {
        "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH",
        "=": "ASSIGN", "(": "LPAREN", ")": "RPAREN",
        "{": "LBRACE", "}": "RBRACE", ";": "SEMICOLON",
        "<": "LT", ">": "GT",
    }
    TWO_CHAR = {"==": "EQ", "!=": "NE", "<=": "LE", ">=": "GE"}

    def __init__(self, source):
        self.source, self.pos, self.line, self.column = source, 0, 1, 1

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self):
        tokens = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isspace():
                self._advance()
                continue
            line, column = self.line, self.column

            if ch.isdigit():
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self._advance()
                tokens.append(Token("NUMBER", self.source[start:self.pos], line, column))
                continue

            if ch.isalpha() or ch == "_":
                start = self.pos
                while self.pos < len(self.source):
                    c = self.source[self.pos]
                    if c.isalnum() or c == "_":
                        self._advance()
                    else:
                        break
                value = self.source[start:self.pos]
                tokens.append(Token(value.upper() if value in self.KEYWORDS else "IDENTIFIER",
                                    value, line, column))
                continue

            two = self.source[self.pos:self.pos + 2]
            if two in self.TWO_CHAR:
                self._advance(); self._advance()
                tokens.append(Token(self.TWO_CHAR[two], two, line, column))
                continue

            if ch in self.SINGLE:
                self._advance()
                tokens.append(Token(self.SINGLE[ch], ch, line, column))
                continue

            raise LexerError(f"Unexpected character '{ch}' at line {line}, column {column}")

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens
