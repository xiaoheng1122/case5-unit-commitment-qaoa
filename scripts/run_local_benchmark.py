"""Run the reproducible local case5 comparison.

The script uses a SciPy MILP/LP reference, ideal CPUQVM state-vector QAOA,
and an offline synthetic-noise CPUQVM rehearsal.  It never contacts a cloud
service and never submits a real-device task.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from case5_unit_commitment import Case5QAOA, load_case5_uc, solve_milp_uc  # noqa: E402


def _solve(instance, backend: str, *, shots: int, maxiter: int, seed: int) -> dict[str, object]:
    result = Case5QAOA(
        instance,
        backend=backend,
        layers=1,
        shots=None if backend == "statevector" else shots,
        seed=seed,
        optimizer_options={"options": {"maxiter": int(maxiter), "disp": False}},
    ).solve(top_k=16, evaluate_method="linprog", enforce_network=True)
    return {
        "backend": result.backend,
        "execution_environment": result.execution_environment,
        "noise_stage": result.noise_stage,
        "logical_qubits": result.logical_qubits,
        "shots": result.shots,
        "feasible_probability": result.feasible_probability,
        "best_cost": result.best_cost,
        "parameters": list(result.parameters),
        "loss": result.loss,
        "best_candidate": None if result.best_candidate is None else result.best_candidate.as_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "latest")
    parser.add_argument("--shots", type=int, default=256)
    parser.add_argument("--maxiter", type=int, default=8)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--skip-noisy", action="store_true")
    args = parser.parse_args()
    if args.shots < 1 or args.maxiter < 1:
        raise SystemExit("shots and maxiter must be positive")

    instance = load_case5_uc()
    reference = solve_milp_uc(instance, evaluate_method="linprog", enforce_network=True)
    if not reference.success or not reference.schedule.success:
        raise RuntimeError(f"classical reference failed: {reference.message}")
    runs = [_solve(instance, "statevector", shots=args.shots, maxiter=args.maxiter, seed=args.seed)]
    if not args.skip_noisy:
        runs.append(_solve(instance, "local_noisy", shots=args.shots, maxiter=max(2, args.maxiter // 2), seed=args.seed))
    reference_cost = float(reference.schedule.total_cost)
    for run in runs:
        best = run["best_cost"]
        run["gap_percent"] = None if best is None else 100.0 * (float(best) - reference_cost) / reference_cost

    payload = {
        "schema_version": "case5_local_benchmark_v1",
        "scope": {
            "real_qpu_submitted": False,
            "remote_quantum_task_submitted": False,
            "execution_environment": "local CPUQVM",
        },
        "case": {
            "name": instance.case.name,
            "source_url": instance.case.source_url,
            "time_periods": instance.time_periods,
            "demand_mw": list(instance.demand_mw),
            "reserve_mw": list(instance.reserve_mw),
        },
        "classical_reference": reference.as_dict(),
        "runs": runs,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "case5_local_benchmark.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [str(run["backend"]) for run in runs]
        values = [float(run["best_cost"]) if run["best_cost"] is not None else float("nan") for run in runs]
        fig, axis = plt.subplots(figsize=(6.8, 3.8))
        axis.bar(labels, values, color=["#4c78a8", "#f58518"][: len(labels)])
        axis.axhline(reference_cost, color="#b23a48", linestyle="--", linewidth=1.6, label="MILP/LP reference")
        axis.set_ylabel("Total cost")
        axis.set_title("IEEE five-bus unit commitment")
        axis.grid(axis="y", alpha=0.25)
        axis.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(args.output / "case5_local_cost_comparison.png", dpi=180)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover - optional plotting dependency
        (args.output / "plot_note.txt").write_text(f"Plot not generated: {exc}\n", encoding="utf-8")
    print(json.dumps({"json": str(path), "reference_cost": reference_cost, "runs": runs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
