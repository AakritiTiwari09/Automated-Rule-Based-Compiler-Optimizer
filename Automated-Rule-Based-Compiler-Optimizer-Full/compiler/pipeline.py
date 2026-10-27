from .lexer import Lexer
from .parser import Parser

def compile_source(source):
    tokens = Lexer(source).tokenize()
    tac = Parser(tokens).parse()
    return tokens, tac
