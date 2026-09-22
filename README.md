# Noisy QAOA for IEEE Five-Bus Unit Commitment

This repository is a compact, reproducible study of unit commitment and
economic dispatch on the MATPOWER five-bus benchmark.  It combines a binary
QUBO commitment model, the QAOA implementation used by the QPanda3 ecosystem,
and a SciPy mixed-integer/linear optimization reference.  An optional OriginQ
Runtime FakeBackend path provides a local, finite-shot rehearsal with device
calibration-derived noise; no real-quantum-processor job is part of this
project.

The project is intended as a readable example that can be run from a clean
Python environment and inspected in the accompanying Notebook.

## Model

The MATPOWER `case5` data provide the buses, generators, branch reactances and
thermal limits.  Five generator commitment variables are used in each of two
periods, giving ten logical qubits.  For a commitment bit `u_{g,t}`, the
available capacity and demand-reserve requirement are represented by the
normalized penalty

$$
W\left(\sum_g \frac{P_g^{\max}}{S_{\rm base}}u_{g,t}
-\frac{D_t+R_t}{S_{\rm base}}\right)^2.
$$

The continuous dispatch stage solves

$$
\min_{p_t}\;\sum_g(a_g p_{g,t}^2+b_g p_{g,t})
\quad\text{subject to}\quad
\sum_g p_{g,t}=D_t,\qquad
P_g^{\min}u_{g,t}\le p_{g,t}\le P_g^{\max}u_{g,t},
$$

and the DC branch-flow limits of the five-bus network.  The reference solves
the commitment and dispatch constraints jointly with
`scipy.optimize.milp` and evaluates the resulting dispatch with
`scipy.optimize.linprog` (or `SLSQP` when quadratic generation costs are
retained).  The QAOA path optimizes the ten-bit commitment distribution and
passes its most relevant feasible states through the same dispatch routine.

![MATPOWER five-bus topology](figures/case5_topology.svg)

The data provenance is the public [MATPOWER `case5.m` benchmark](https://github.com/MATPOWER/matpower/blob/master/data/case5.m).

## Backends and scope

Three local modes are available through `BackendConfig`:

- `statevector`: exact probabilities from the local pyqpanda3 CPUQVM;
- `local_fake`: finite-shot sampling without gate noise;
- `local_noisy`: finite shots plus a named synthetic gate/readout noise profile.

For the OriginQ Runtime rehearsal, `RuntimeFakeBackendRunner` calls
`RuntimeService -> QDevice -> FakeBackend -> transpile -> sample`.  This is a
local FakeBackend execution path and does not create a remote task.  The API
key is read only from the environment variable selected by the caller; its
value is never printed, stored, or committed.  A Runtime installation is
optional and is not needed for the ordinary Notebook or local benchmark.

## Installation

Python 3.10 or newer is supported.  The core workflow needs NumPy, SciPy,
SymPy, and pyqpanda3; Matplotlib and pytest are development extras.

```powershell
python -m pip install -e ".[dev]"
```

The optional Runtime rehearsal additionally needs the OriginQ
`qpanda3_runtime` package available in the local environment.

## Quick start

Run the classical reference, ideal state-vector QAOA, and local synthetic-noise
comparison:

```powershell
python scripts\run_local_benchmark.py --output results\latest
```

The command writes `case5_local_benchmark.json` and, when Matplotlib is
available, `case5_local_cost_comparison.png`.  The included record uses the
MILP/LP reference cost 28439.31 in the case5 cost units.  QAOA results depend
on the optimizer iteration limit and random seed; the JSON records both so
that a run can be reproduced.

Open `notebooks/case5_unit_commitment_workflow.ipynb` for the derivation,
classical reference, QAOA solution, dispatch comparison, and the offline noisy
CPUQVM example.

An inspected Runtime FakeBackend record is included in
[`results/runtime_fakebackend/`](results/runtime_fakebackend/).  It is clearly
marked as a local rehearsal and contains no credential or remote task payload.

To use the Runtime FakeBackend adapter with a caller-owned key, set the key in
the caller's environment and run:

```powershell
$env:QPANDA3_API_KEY = "<your-OriginQ-api-key>"
python scripts\run_fakebackend.py --hardware-name WK_C180 --shots 256 --maxiter 4 `
  --output results\runtime_fakebackend
```

The placeholder above is not a credential.  Do not replace it in committed
files, notebooks, or logs.  The result record stores only the environment
variable name and a boolean presence flag.

## Package API

```python
from case5_unit_commitment import Case5QAOA, load_case5_uc, solve_milp_uc

instance = load_case5_uc()
reference = solve_milp_uc(instance, evaluate_method="linprog")
quantum = Case5QAOA(
    instance,
    backend="statevector",
    layers=1,
    seed=11,
    optimizer_options={"options": {"maxiter": 25, "disp": False}},
).solve(top_k=16, evaluate_method="linprog")
print(reference.schedule.total_cost, quantum.best_cost)
```

The public facade keeps model construction, classical dispatch, QAOA sampling,
and optional Runtime FakeBackend execution separate, so each stage can be
audited independently.

## Reproducibility and limitations

- The benchmark is deliberately small and is a validation example rather than
  a claim of quantum speed-up.
- QAOA parameter optimization is performed locally; the noisy Runtime path
  samples a final measured circuit and does not optimize on hardware.
- Runtime calibration units for T1/T2 are reported by the adapter as metadata;
  no undocumented conversion is silently applied by default.
- Results are finite-shot estimates whenever a sampled backend is selected.

## References

1. F. Li and R. Bo, “DCOPF-based LMP simulation: Algorithm, implementation
   and example,” IEEE PES General Meeting, 2010.
2. E. Farhi, J. Goldstone, and S. Gutmann, “A Quantum Approximate Optimization
   Algorithm,” arXiv:1411.4028, 2014.
3. L. Zhou *et al.*, “Quantum Approximate Optimization Algorithm:
   Performance, Mechanism, and Implementation on Near-Term Devices,” *Physical
   Review X*, 10, 021067, 2020.
4. MATPOWER, “case5.m,”
   [MATPOWER data repository](https://github.com/MATPOWER/matpower/blob/master/data/case5.m).
5. Origin Quantum, [QPanda3 documentation](https://github.com/OriginQ/QPanda3-doc).

## License

The project is released under the Apache License 2.0.  See [LICENSE](LICENSE).

