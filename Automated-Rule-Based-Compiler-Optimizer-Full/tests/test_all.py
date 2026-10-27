from compiler.pipeline import compile_source
from compiler.interpreter import TACInterpreter
from optimizers.engine import OptimizationEngine

def run(source, inputs=None):
    _, tac = compile_source(source)
    opt, info = OptimizationEngine().optimize(tac.instructions)
    a = TACInterpreter().execute(tac.instructions, inputs or [])
    b = TACInterpreter().execute(opt, inputs or [])
    assert a["output_text"] == b["output_text"], (a, b, tac.to_text(), info)
    return tac, opt

def test_all_arithmetic_optimizations():
    source = """
    input a;
    t1 = 10 * 20;
    t2 = a + 0;
    t3 = t2 * 1;
    t4 = a + 0;
    t5 = a * 2;
    dead = t1 + t3;
    print t4;
    print t5;
    """
    run(source, [7])

def test_loop():
    source = """
    i = 0;
    s = 0;
    while (i < 5) {
        x = i * 2;
        s = s + x;
        i = i + 1;
    }
    print s;
    """
    run(source)

def test_if_else():
    source = """
    input a;
    if (a > 5) {
        x = 10;
    } else {
        x = 20;
    }
    print x;
    """
    run(source, [7])
    run(source, [3])
