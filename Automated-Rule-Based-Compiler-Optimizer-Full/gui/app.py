import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import runpy
import json
import urllib.error
import urllib.request

from compiler.pipeline import compile_source
from compiler.interpreter import TACInterpreter
from optimizers.engine import OptimizationEngine
from metrics import count_metrics, reduction

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

GRAPH_FILES = [
    ("Instruction Count", "instruction_before_after.png"),
    ("Optimizer Effectiveness", "optimizer_effectiveness.png"),
    ("Convergence / Passes", "convergence.png"),
    ("Optimizer Distribution", "optimizer_distribution.png"),
    ("Code Size vs Execution Proxy", "code_size_vs_execution_proxy.png"),
    ("Optimizer × Category Heatmap", "optimizer_category_heatmap.png"),
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automated Rule-Based Compiler Code Optimizer")
        self.geometry("1400x900")
        self.minsize(1100, 750)

        self.last_tac = None
        self.last_optimized = None
        self.baseline_output = None
        self.baseline_metrics = None
        self.last_source = ""
        self.last_api_result = None
        self.last_original_execution = None
        self.last_optimized_execution = None
        self.last_verdict = None
        self.graph_images = []

        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(15, 10, 15, 5))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            header,
            text="AUTOMATED RULE-BASED COMPILER CODE OPTIMIZER",
            font=("Arial", 22, "bold")
        ).pack()
        ttk.Label(
            header,
            text="Source → Lexer → Parser → TAC → Optimization → Verification",
            font=("Arial", 10)
        ).pack(pady=(2, 0))

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self.compiler_tab = ttk.Frame(self.tabs)
        self.analytics_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.compiler_tab, text="Compiler & Optimizer")
        self.tabs.add(self.analytics_tab, text="Benchmark & Analytics")

        self._build_compiler_tab()
        self._build_analytics_tab()

    # ---------------- Compiler tab ----------------

    def _build_compiler_tab(self):
        tab = self.compiler_tab
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        # Reserve enough vertical room for all three work areas.
        tab.rowconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        tab.rowconfigure(2, weight=0, minsize=205)
        tab.rowconfigure(3, weight=0)
        tab.rowconfigure(4, weight=0)

        source_frame = ttk.LabelFrame(tab, text="1. Source Program", padding=5)
        source_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        original_frame = ttk.LabelFrame(tab, text="2. Original Three Address Code (TAC)", padding=5)
        original_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        optimized_frame = ttk.LabelFrame(tab, text="3. Optimized TAC", padding=5)
        optimized_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=4)

        result_frame = ttk.LabelFrame(tab, text="4. Optimization Log / Metrics", padding=5)
        result_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=4)

        self.source = tk.Text(source_frame, font=("Consolas", 11), wrap="none")
        self.source.pack(fill="both", expand=True)
        self.source.insert(
            "1.0",
            "x = 10 * 20;\n"
            "y = x + 5;\n"
            "z = y * 1;\n"
            "a = z + 0;\n"
            "print a;\n"
        )

        self.original_box = tk.Text(
            original_frame, font=("Consolas", 11), wrap="none",
            state="disabled"
        )
        self.original_box.pack(fill="both", expand=True)

        self.optimized_box = tk.Text(
            optimized_frame, font=("Consolas", 11), wrap="none",
            state="disabled"
        )
        self.optimized_box.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            result_frame, font=("Consolas", 10), wrap="word",
            state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        # 5. Separate pre-optimization testing panel
        pretest_frame = ttk.LabelFrame(
            tab, text="5. Pre-Optimization Testing", padding=6
        )
        pretest_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew",
            padx=8, pady=(4, 5)
        )
        # Prevent the test output and button from being squeezed out of view.
        pretest_frame.configure(height=205)
        pretest_frame.grid_propagate(False)
        pretest_frame.columnconfigure(0, weight=1)
        pretest_frame.rowconfigure(1, weight=1)

        ttk.Label(
            pretest_frame,
            text=(
                "Run the original TAC before optimization. Use the Input values "
                "field below (comma-separated for multiple values)."
            ),
            font=("Arial", 9)
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        pretest_text_frame = ttk.Frame(pretest_frame)
        pretest_text_frame.grid(row=1, column=0, sticky="nsew")
        pretest_text_frame.columnconfigure(0, weight=1)
        pretest_text_frame.rowconfigure(0, weight=1)

        self.pretest_box = tk.Text(
            pretest_text_frame, font=("Consolas", 10), wrap="word",
            height=6, state="disabled"
        )
        self.pretest_box.grid(row=0, column=0, sticky="nsew")

        pretest_scrollbar = ttk.Scrollbar(
            pretest_text_frame, orient="vertical",
            command=self.pretest_box.yview
        )
        pretest_scrollbar.grid(row=0, column=1, sticky="ns")
        self.pretest_box.configure(yscrollcommand=pretest_scrollbar.set)

        ttk.Button(
            pretest_frame,
            text="Test Before Optimization",
            command=self.test_before_optimization
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        controls = ttk.LabelFrame(tab, text="Controls", padding=7)
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        for label, command in [
            ("① Generate TAC", self.generate),
            ("② Optimize", self.optimize),
            ("③ Run Original", self.run_original),
            ("④ Run Optimized", self.run_optimized),
        ]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=4)

        ttk.Button(controls, text="Export Full Report", command=self.export_optimized).pack(side="left", padx=4)
        ttk.Button(controls, text="Export Optimized TAC", command=self.export_optimized_tac).pack(side="left", padx=4)
        ttk.Button(controls, text="Clear", command=self.clear).pack(side="left", padx=4)

        ttk.Label(controls, text="Input values:").pack(side="left", padx=(20, 4))
        self.inputs = ttk.Entry(controls, width=18)
        self.inputs.insert(0, "5")
        self.inputs.pack(side="left")

        status_frame = ttk.Frame(tab, padding=(8, 0, 8, 7))
        status_frame.grid(row=4, column=0, columnspan=2, sticky="ew")

        self.status = ttk.Label(
            status_frame,
            text="Ready — click Generate TAC to begin.",
            font=("Arial", 10, "bold")
        )
        self.status.pack(side="left")

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _parse_inputs(self):
        value = self.inputs.get().strip()
        if not value:
            return []
        return [int(x.strip()) for x in value.split(",") if x.strip()]

    def generate(self):
        try:
            source = self.source.get("1.0", "end").strip()
            if not source:
                raise ValueError("Enter a source program first.")

            _, tac = compile_source(source)
            self.last_tac = tac
            self.last_source = source
            self.last_optimized = None
            self.baseline_output = None
            self.baseline_metrics = None
            self.last_api_result = None
            self.last_original_execution = None
            self.last_optimized_execution = None
            self.last_verdict = None

            self._set_text(self.original_box, tac.to_text())
            self._set_text(self.optimized_box, "")
            self._set_text(self.log_box, "")
            self._set_text(self.pretest_box, "")

            self.status.config(
                text=f"✓ TAC generated successfully — {len(tac.instructions)} instructions."
            )
        except Exception as exc:
            messagebox.showerror("Compilation Error", str(exc))
            self.status.config(text="✗ Compilation failed.")

    def test_before_optimization(self):
        """Execute the original, unoptimized TAC and show baseline results."""
        try:
            if self.last_tac is None:
                self.generate()
            if self.last_tac is None:
                return

            inputs = self._parse_inputs()
            result = TACInterpreter().execute(
                self.last_tac.instructions, inputs
            )
            output = result["output_text"]
            metrics = count_metrics(
                self.last_tac.instructions,
                self.last_tac.format_instruction
            )

            self.baseline_output = output
            self.baseline_metrics = metrics
            self.last_original_execution = {
                "output": output,
                "inputs": inputs,
                "success": True,
                "stage": "Pre-optimization test"
            }

            display = [
                "PRE-OPTIMIZATION TEST RESULTS",
                "=============================",
                "",
                f"Input Values: {inputs}",
                "",
                "ORIGINAL PROGRAM OUTPUT",
                "-----------------------",
                output if output else "(no print output)",
                "",
                "BASELINE METRICS",
                "----------------",
                f"Instruction Count : {metrics['instruction_count']}",
                f"Operation Count   : {metrics['operation_count']}",
                f"Temporary Count   : {metrics['temporary_count']}",
                f"Code Size         : {metrics['code_size']} characters",
                "",
                "STATUS: ORIGINAL PROGRAM EXECUTED SUCCESSFULLY"
            ]
            self._set_text(self.pretest_box, "\n".join(display))
            self.status.config(
                text=("✓ Pre-optimization test completed — output: "
                      f"{output or '(no output)'}")
            )
        except Exception as exc:
            messagebox.showerror("Pre-Optimization Testing Error", str(exc))
            self.status.config(text="✗ Pre-optimization testing failed.")

    def optimize(self):
        """Send the current source program to the FastAPI service over HTTP."""
        try:
            source = self.source.get("1.0", "end").strip()
            if not source:
                raise ValueError("Enter a source program first.")

            # Keep the local TAC available for the existing execution and metrics features.
            _, tac = compile_source(source)
            self.last_tac = tac
            self.last_source = source
            self.last_original_execution = None
            self.last_optimized_execution = None
            self.last_verdict = None

            payload = {
                "source": source,
                "inputs": self._parse_inputs(),
                "max_passes": 20
            }
            request = urllib.request.Request(
                "http://127.0.0.1:8000/optimize",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                try:
                    detail = json.loads(detail).get("detail", detail)
                except (json.JSONDecodeError, AttributeError):
                    pass
                raise RuntimeError(
                    f"API returned HTTP {exc.code}: {detail}"
                ) from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(
                    "Could not connect to the FastAPI server at "
                    "http://127.0.0.1:8000. Start it first with:\n"
                    "python -m uvicorn api:app --reload"
                ) from exc


            optimized = result["optimized_instructions"]
            info = result["optimization_report"]
            self.last_optimized = optimized
            self.last_api_result = result

            self._set_text(self.original_box, result["original_tac"])
            self._set_text(self.optimized_box, result["optimized_tac"])

            before = count_metrics(tac.instructions, tac.format_instruction)
            after = count_metrics(optimized, tac.format_instruction)

            lines = ["OPTIMIZATION RESULTS", "====================", ""]
            total_changes = 0

            for item in info["logs"]:
                total_changes += item["count"]
                lines.append(f"✓ {item['optimizer']} ({item['count']} change(s))")
                for change in item["changes"][:8]:
                    lines.append(f"   • {change}")
                lines.append("")

            lines.extend([
                "METRICS",
                "-------",
                f"Instructions : {before['instruction_count']} → {after['instruction_count']} "
                f"({reduction(before['instruction_count'], after['instruction_count']):.1f}% reduction)",
                f"Operations   : {before['operation_count']} → {after['operation_count']} "
                f"({reduction(before['operation_count'], after['operation_count']):.1f}% reduction)",
                f"Temporaries  : {before['temporary_count']} → {after['temporary_count']} "
                f"({reduction(before['temporary_count'], after['temporary_count']):.1f}% reduction)",
                f"Code Size    : {before['code_size']} → {after['code_size']} "
                f"({reduction(before['code_size'], after['code_size']):.1f}% reduction)",
                f"Optimization Passes: {info['passes']}",
                f"Total Changes: {total_changes}",
                "",
                f"API Verification: {result['verification']}",
                f"Original Output : {result['original_output'] or '(no output)'}",
                f"Optimized Output: {result['optimized_output'] or '(no output)'}",
                "",
                "Use Run Original / Run Optimized for another execution check."
            ])

            self._set_text(self.log_box, "\n".join(lines))
            self.status.config(
                text=f"✓ Optimization complete — {total_changes} change(s), "
                     f"{info['passes']} pass(es); API verification: {result['verification']}."
            )
        except Exception as exc:
            messagebox.showerror("Optimization Error", str(exc))
            self.status.config(text="✗ Optimization failed.")

    def export_optimized(self):
        """Export the complete compiler optimization and testing report."""
        if self.last_tac is None or self.last_optimized is None:
            messagebox.showwarning("Nothing to Export", "Run Optimize first.")
            return

        target = filedialog.asksaveasfilename(
            title="Export Full Compiler Report",
            defaultextension=".txt",
            filetypes=[("Text report", "*.txt"), ("All files", "*.*")]
        )
        if not target:
            return

        try:
            source = self.last_source or self.source.get("1.0", "end").strip()
            inputs = self._parse_inputs()
            original_tac = self.last_tac.to_text()
            optimized_tac = self.last_tac.to_text(self.last_optimized)

            # Use execution results already recorded in the GUI/API. If execution
            # buttons were not used, the API's optimization response is still a
            # real result from the backend and is included as the execution output.
            api_result = self.last_api_result or {}
            original_exec = self.last_original_execution
            optimized_exec = self.last_optimized_execution

            original_output = (
                original_exec.get("output") if original_exec is not None
                else api_result.get("original_output", self.baseline_output)
            )
            optimized_output = (
                optimized_exec.get("output") if optimized_exec is not None
                else api_result.get("optimized_output")
            )
            verification = self.last_verdict or api_result.get("verification", "Not recorded")
            report = api_result.get("optimization_report", {})
            logs = report.get("logs", []) if isinstance(report, dict) else []

            before = count_metrics(self.last_tac.instructions, self.last_tac.format_instruction)
            after = count_metrics(self.last_optimized, self.last_tac.format_instruction)

            sections = [
                "=" * 72,
                "       AUTOMATED RULE-BASED COMPILER CODE OPTIMIZER",
                "                    FULL EXECUTION REPORT",
                "=" * 72,
                "",
                "1. ORIGINAL SOURCE CODE",
                "-" * 72,
                source or "(not available)",
                "",
                "2. PRE-OPTIMIZATION TESTING",
                "-" * 72,
                f"Input Values: {inputs}",
                f"Test Result: {'Executed' if original_output is not None else 'Not recorded'}",
                "Original Program Output:",
                str(original_output) if original_output not in (None, "") else "(no print output / not recorded)",
                "",
                "3. ORIGINAL THREE ADDRESS CODE (TAC)",
                "-" * 72,
                original_tac or "(not available)",
                "",
                "4. OPTIMIZED THREE ADDRESS CODE (TAC)",
                "-" * 72,
                optimized_tac or "(not available)",
                "",
                "5. OPTIMIZATION RULES / CHANGES",
                "-" * 72,
            ]

            if logs:
                for item in logs:
                    sections.append(
                        f"- {item.get('optimizer', 'Optimizer')}: "
                        f"{item.get('count', 0)} change(s)"
                    )
                    for change in item.get("changes", [])[:8]:
                        sections.append(f"    • {change}")
            else:
                sections.append("No detailed optimization log was recorded.")

            sections.extend([
                "",
                "6. ORIGINAL PROGRAM EXECUTION",
                "-" * 72,
                f"Inputs: {original_exec.get('inputs', inputs) if original_exec else inputs}",
                f"Output: {str(original_output) if original_output not in (None, '') else '(no output / not recorded)'}",
                "",
                "7. OPTIMIZED PROGRAM EXECUTION",
                "-" * 72,
                f"Inputs: {optimized_exec.get('inputs', inputs) if optimized_exec else inputs}",
                f"Output: {str(optimized_output) if optimized_output not in (None, '') else '(no output / not recorded)'}",
                "",
                "8. EQUIVALENCE VERIFICATION",
                "-" * 72,
                f"Original Output : {str(original_output) if original_output not in (None, '') else '(no output / not recorded)'}",
                f"Optimized Output: {str(optimized_output) if optimized_output not in (None, '') else '(no output / not recorded)'}",
                f"Verification Status: {verification}",
                "",
                "9. OPTIMIZATION METRICS",
                "-" * 72,
                f"Instruction Count : {before['instruction_count']} -> {after['instruction_count']} "
                f"({reduction(before['instruction_count'], after['instruction_count']):.1f}% reduction)",
                f"Operation Count   : {before['operation_count']} -> {after['operation_count']} "
                f"({reduction(before['operation_count'], after['operation_count']):.1f}% reduction)",
                f"Temporary Count   : {before['temporary_count']} -> {after['temporary_count']} "
                f"({reduction(before['temporary_count'], after['temporary_count']):.1f}% reduction)",
                f"Code Size         : {before['code_size']} -> {after['code_size']} "
                f"({reduction(before['code_size'], after['code_size']):.1f}% reduction)",
                f"Optimization Passes: {report.get('passes', 'N/A')}",
                "",
                "=" * 72,
                "                       END OF REPORT",
                "=" * 72,
                ""
            ])

            Path(target).write_text("\\n".join(sections), encoding="utf-8")
            messagebox.showinfo("Export Complete", f"Full report saved to:\\n{target}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def export_optimized_tac(self):
        """Export only the optimized TAC, separately from the full report."""
        if self.last_optimized is None or self.last_tac is None:
            messagebox.showwarning("Nothing to Export", "Run Optimize first.")
            return

        target = filedialog.asksaveasfilename(
            title="Export Optimized TAC",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not target:
            return

        try:
            Path(target).write_text(
                self.last_tac.to_text(self.last_optimized),
                encoding="utf-8"
            )
            messagebox.showinfo("Export Complete", f"Optimized TAC saved to:\\n{target}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def run_original(self):
        try:
            if self.last_tac is None:
                self.generate()
            if self.last_tac is None:
                return

            inputs = self._parse_inputs()
            result = TACInterpreter().execute(self.last_tac.instructions, inputs)
            output = result["output_text"]
            self.last_original_execution = {
                "output": output,
                "inputs": inputs,
                "success": True,
                "stage": "Run Original"
            }
            self.baseline_output = output
            self.status.config(text=f"✓ Original execution output: {output or '(no output)'}")
        except Exception as exc:
            messagebox.showerror("Execution Error", str(exc))
            self.status.config(text="✗ Original execution failed.")

    def run_optimized(self):
        try:
            if self.last_tac is None:
                self.generate()
            if self.last_optimized is None:
                self.optimize()

            if self.last_tac is None or self.last_optimized is None:
                return

            inputs = self._parse_inputs()
            original = TACInterpreter().execute(self.last_tac.instructions, inputs)
            optimized = TACInterpreter().execute(self.last_optimized, inputs)

            original_output = original["output_text"]
            optimized_output = optimized["output_text"]
            verdict = "PASS" if original_output == optimized_output else "FAIL"
            self.last_original_execution = {
                "output": original_output,
                "inputs": inputs,
                "success": True,
                "stage": "Run Original comparison"
            }
            self.last_optimized_execution = {
                "output": optimized_output,
                "inputs": inputs,
                "success": True,
                "stage": "Run Optimized"
            }
            self.last_verdict = verdict

            log = self.log_box.get("1.0", "end").strip()
            verification = (
                "\n\nOUTPUT VERIFICATION\n"
                "===================\n"
                f"Original Output : {original_output or '(no output)'}\n"
                f"Optimized Output: {optimized_output or '(no output)'}\n"
                f"VERDICT         : {'✓ PASS — Outputs are identical' if verdict == 'PASS' else '✗ FAIL — Outputs differ'}"
            )
            self._set_text(self.log_box, log + verification)

            # Keep the baseline test visible and append the comparison result there too.
            pretest_text = self.pretest_box.get("1.0", "end").strip()
            if pretest_text:
                pretest_text += (
                    "\n\nOPTIMIZATION VERIFICATION\n"
                    "==========================\n"
                    f"Original Output : {original_output or '(no output)'}\n"
                    f"Optimized Output: {optimized_output or '(no output)'}\n"
                    f"VERDICT: {verdict} — "
                    + ("Outputs match." if verdict == "PASS" else "Outputs differ.")
                )
                self._set_text(self.pretest_box, pretest_text)

            self.status.config(
                text=(
                    "✓ OUTPUT MATCH: PASS — Original and optimized programs are equivalent."
                    if verdict == "PASS"
                    else "✗ OUTPUT MATCH: FAIL — Optimization changed the output."
                )
            )
        except Exception as exc:
            messagebox.showerror("Execution Error", str(exc))
            self.status.config(text="✗ Optimized execution failed.")

    def clear(self):
        self.source.delete("1.0", "end")
        self._set_text(self.original_box, "")
        self._set_text(self.optimized_box, "")
        self._set_text(self.log_box, "")
        self._set_text(self.pretest_box, "")
        self.last_tac = None
        self.last_optimized = None
        self.baseline_output = None
        self.baseline_metrics = None
        self.last_source = ""
        self.last_api_result = None
        self.last_original_execution = None
        self.last_optimized_execution = None
        self.last_verdict = None
        self.status.config(text="Ready — enter a source program.")

    # ---------------- Analytics tab ----------------

    def _build_analytics_tab(self):
        tab = self.analytics_tab
        tab.columnconfigure(0, weight=1)
        # Reserve rows for dashboard cards/table; let only graphs expand.
        tab.rowconfigure(3, weight=1)

        top = ttk.Frame(tab, padding=10)
        top.grid(row=0, column=0, sticky="ew")

        ttk.Label(
            top,
            text="100-Program Benchmark & Analytics Dashboard",
            font=("Arial", 17, "bold")
        ).pack(anchor="w")

        ttk.Label(
            top,
            text="Generate the benchmark → run it → generate charts. The charts will appear below inside the GUI."
        ).pack(anchor="w", pady=(2, 8))

        button_bar = ttk.Frame(top)
        button_bar.pack(anchor="w")

        ttk.Button(
            button_bar, text="1. Generate 100-Program Dataset",
            command=self.generate_dataset
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            button_bar, text="2. Run Benchmark",
            command=self.run_benchmark
        ).pack(side="left", padx=6)

        ttk.Button(
            button_bar, text="3. Generate & Show Graphs",
            command=self.generate_graphs
        ).pack(side="left", padx=6)

        ttk.Button(
            button_bar, text="Refresh Graphs",
            command=self.load_graphs
        ).pack(side="left", padx=6)

        # Benchmark summary cards (restored)
        self.summary_frame = ttk.LabelFrame(tab, text="Benchmark Results Summary", padding=8)
        self.summary_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        for col in range(6):
            self.summary_frame.columnconfigure(col, weight=1)
        self.summary_vars = {}
        summary_items = [
            ("Programs", "programs"),
            ("Test Cases", "test_cases"),
            ("Correctness", "correctness"),
            ("Avg Instruction Reduction", "instruction_reduction"),
            ("Avg Operation Reduction", "operation_reduction"),
            ("Avg Temporary Reduction", "temporary_reduction"),
        ]
        for col, (label, key) in enumerate(summary_items):
            card = ttk.Frame(self.summary_frame, relief="ridge", borderwidth=1, padding=8)
            card.grid(row=0, column=col, sticky="ew", padx=3)
            ttk.Label(card, text=label, font=("Arial", 9, "bold")).pack()
            var = tk.StringVar(value="—")
            self.summary_vars[key] = var
            ttk.Label(card, textvariable=var, font=("Arial", 15, "bold")).pack(pady=(4, 0))

        # Category-wise results table (restored)
        table_frame = ttk.LabelFrame(tab, text="Category-wise Results", padding=6)
        table_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        table_frame.columnconfigure(0, weight=1)
        columns = ("category", "programs", "before", "after", "reduction")
        self.category_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
        headings = {"category": "Category", "programs": "Programs", "before": "Avg TAC Before",
                    "after": "Avg TAC After", "reduction": "Reduction"}
        widths = {"category": 260, "programs": 100, "before": 180, "after": 180, "reduction": 140}
        for col in columns:
            self.category_table.heading(col, text=headings[col])
            self.category_table.column(col, width=widths[col], anchor="center")
        self.category_table.pack(fill="x", expand=True)

        # Scrollable graph dashboard
        outer = ttk.Frame(tab)
        outer.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        self.graph_canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.graph_canvas.yview)
        self.graph_canvas.configure(yscrollcommand=scrollbar.set)

        self.graph_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.graph_frame = ttk.Frame(self.graph_canvas)
        self.graph_window = self.graph_canvas.create_window(
            (0, 0), window=self.graph_frame, anchor="nw"
        )

        self.graph_frame.bind(
            "<Configure>",
            lambda e: self.graph_canvas.configure(
                scrollregion=self.graph_canvas.bbox("all")
            )
        )
        self.graph_canvas.bind(
            "<Configure>",
            self._resize_graph_frame
        )

        self.graph_images = []
        self.show_graph_placeholder()

    def _resize_graph_frame(self, event):
        self.graph_canvas.itemconfigure(self.graph_window, width=event.width)

    def show_graph_placeholder(self):
        for child in self.graph_frame.winfo_children():
            child.destroy()

        ttk.Label(
            self.graph_frame,
            text=(
                "Analytics Dashboard\n\n"
                "1. Generate the 100-program dataset\n"
                "2. Run the benchmark\n"
                "3. Click 'Generate & Show Graphs'\n\n"
                "All six project graphs will then appear here."
            ),
            font=("Arial", 13),
            justify="center"
        ).pack(pady=120)

    def update_summary(self):
        """Refresh summary cards and category table from benchmark_summary.json."""
        path = RESULTS / "benchmark_summary.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Results Error", f"Could not read benchmark summary:\n{exc}")
            return

        total_programs = int(data.get("total_programs", data.get("programs", 0)) or 0)
        total_tests = int(data.get("total_tests", data.get("tests", data.get("test_cases", 0))) or 0)
        passed = int(data.get("passed", data.get("tests_passed", 0)) or 0)
        correctness = 100.0 * passed / total_tests if total_tests else 0.0
        categories = data.get("category_totals", data.get("categories", {}))
        if not isinstance(categories, dict):
            categories = {}

        total_before = sum(float(v.get("before", v.get("total_before", 0)) or 0)
                           for v in categories.values() if isinstance(v, dict))
        total_after = sum(float(v.get("after", v.get("total_after", 0)) or 0)
                          for v in categories.values() if isinstance(v, dict))
        # Use benchmark.py's average-of-program-percentages value (13.00%).
        # Fall back to pooled reduction only for older summary files.
        instr_pct = data.get("instruction_reduction")
        if instr_pct is None:
            instr_pct = (100.0 * (total_before - total_after) / total_before
                         if total_before else 0.0)
        instr_pct = float(instr_pct)

        # Per-program benchmark CSV supplies operation and temporary metrics.
        op_b = op_a = tmp_b = tmp_a = 0.0
        csv_path = RESULTS / "benchmark_results.csv"
        if csv_path.exists():
            import csv
            with csv_path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    for key, target in (("before_operations", "op_b"), ("after_operations", "op_a"),
                                         ("before_temporaries", "tmp_b"), ("after_temporaries", "tmp_a")):
                        try: value = float(row.get(key, 0) or 0)
                        except (TypeError, ValueError): value = 0.0
                        if target == "op_b": op_b += value
                        elif target == "op_a": op_a += value
                        elif target == "tmp_b": tmp_b += value
                        else: tmp_a += value
        # Prefer the dashboard's same per-program average convention as benchmark.py.
        op_pct = data.get("operation_reduction")
        if op_pct is None:
            op_pct = 100.0 * (op_b - op_a) / op_b if op_b else None
        else:
            op_pct = float(op_pct)

        tmp_pct = data.get("temporary_reduction")
        if tmp_pct is None:
            tmp_pct = 100.0 * (tmp_b - tmp_a) / tmp_b if tmp_b else None
        else:
            tmp_pct = float(tmp_pct)

        self.summary_vars["programs"].set(str(total_programs))
        self.summary_vars["test_cases"].set(str(total_tests))
        self.summary_vars["correctness"].set(f"{correctness:.1f}%")
        self.summary_vars["instruction_reduction"].set(f"{instr_pct:.1f}%")
        self.summary_vars["operation_reduction"].set(f"{op_pct:.1f}%" if op_pct is not None else "N/A")
        self.summary_vars["temporary_reduction"].set(f"{tmp_pct:.1f}%" if tmp_pct is not None else "N/A")

        for item in self.category_table.get_children():
            self.category_table.delete(item)
        order = ["cat1_constant", "cat2_algebraic", "cat3_dead_code", "cat4_cse", "cat5_loops"]
        names = {"cat1_constant": "Constant Expressions", "cat2_algebraic": "Algebraic Redundancy",
                 "cat3_dead_code": "Dead Code", "cat4_cse": "Repeated Expressions (CSE)",
                 "cat5_loops": "Loop-Based Programs"}
        for cat in order:
            v = categories.get(cat)
            if not isinstance(v, dict):
                continue
            n = int(v.get("programs", v.get("count", 20)) or 0)
            before = float(v.get("before", v.get("total_before", 0)) or 0)
            after = float(v.get("after", v.get("total_after", 0)) or 0)
            avg_b = before / n if n else 0.0
            avg_a = after / n if n else 0.0
            pct = 100.0 * (avg_b-avg_a)/avg_b if avg_b else 0.0
            self.category_table.insert("", "end", values=(names.get(cat, cat), n, f"{avg_b:.2f}", f"{avg_a:.2f}", f"{pct:.1f}%"))

    def generate_dataset(self):
        try:
            runpy.run_path(
                str(ROOT / "dataset" / "generate_dataset.py"),
                run_name="__main__"
            )
            count = len(list((ROOT / "dataset").glob("cat*/*.json")))
            messagebox.showinfo(
                "Dataset Ready",
                f"Generated {count} benchmark programs.\n\n"
                "Next click 'Run Benchmark'."
            )
        except Exception as exc:
            messagebox.showerror("Dataset Error", str(exc))

    def run_benchmark(self):
        try:
            runpy.run_path(
                str(ROOT / "benchmark.py"),
                run_name="__main__"
            )
            summary = RESULTS / "benchmark_summary.json"
            if summary.exists():
                self.update_summary()
                messagebox.showinfo(
                    "Benchmark Complete",
                    "Benchmark completed successfully.\n\n"
                    "Next click 'Generate & Show Graphs'."
                )
            else:
                raise FileNotFoundError("benchmark_summary.json was not generated.")
        except Exception as exc:
            messagebox.showerror("Benchmark Error", str(exc))

    def generate_graphs(self):
        try:
            from visualization import make_plots
            make_plots(str(RESULTS))
            self.update_summary()
            self.load_graphs()
            self.tabs.select(self.analytics_tab)
        except Exception as exc:
            messagebox.showerror("Graph Error", str(exc))

    def load_graphs(self):
        self.update_summary()
        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "Pillow is required to display graphs.\n\n"
                "Run: pip install -r requirements.txt"
            )
            return

        missing = [filename for _, filename in GRAPH_FILES if not (RESULTS / filename).exists()]
        if missing:
            self.show_graph_placeholder()
            messagebox.showwarning(
                "Graphs Not Generated",
                "Generate the dataset, run the benchmark, then click "
                "'Generate & Show Graphs'."
            )
            return

        for child in self.graph_frame.winfo_children():
            child.destroy()

        self.graph_images = []

        # Two-column dashboard.
        self.graph_frame.columnconfigure(0, weight=1)
        self.graph_frame.columnconfigure(1, weight=1)

        for index, (title, filename) in enumerate(GRAPH_FILES):
            row = index // 2
            col = index % 2

            card = ttk.LabelFrame(
                self.graph_frame,
                text=title,
                padding=8
            )
            card.grid(
                row=row, column=col,
                sticky="nsew",
                padx=7, pady=7
            )

            image = Image.open(RESULTS / filename).convert("RGB")
            image.thumbnail((620, 360), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.graph_images.append(photo)

            label = ttk.Label(card, image=photo)
            label.pack(expand=True)

            ttk.Label(
                card,
                text=filename,
                font=("Arial", 8)
            ).pack(pady=(4, 0))

        self.graph_canvas.update_idletasks()
        self.graph_canvas.configure(scrollregion=self.graph_canvas.bbox("all"))
        self.status_update_analytics(
            f"✓ Six analytics graphs are displayed inside the GUI."
        )

    def status_update_analytics(self, message):
        # Reuse the main window title briefly as feedback without interrupting the dashboard.
        self.title(f"Automated Rule-Based Compiler Code Optimizer — {message}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
