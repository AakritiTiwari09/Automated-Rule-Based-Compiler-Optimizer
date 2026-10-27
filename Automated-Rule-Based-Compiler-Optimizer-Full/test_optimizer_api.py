
from optimizer_api import optimize_source

source = """
a = 10;
b = 20;
c = a + b;
print c;
"""

result = optimize_source(source)

print("\n========== ORIGINAL TAC ==========")
print(result["original_tac"])

print("\n========== OPTIMIZED TAC ==========")
print(result["optimized_tac"])

print("\n========== OPTIMIZATION REPORT ==========")
print(result["optimization_report"])

print("\n========== RESULTS ==========")
print("Instructions before:", result["instructions_before"])
print("Instructions after:", result["instructions_after"])
print("Instruction reduction:",
      result["instruction_reduction_percent"], "%")
print("Original output:", result["original_output"])
print("Optimized output:", result["optimized_output"])
print("Verification:", result["verification"])
