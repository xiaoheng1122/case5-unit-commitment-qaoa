import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_notebook_is_valid_json_and_has_formula_sections():
    notebook = json.loads((ROOT / "notebooks" / "case5_unit_commitment_workflow.ipynb").read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "MILP" in source
    assert "local_noisy" in source
    assert "\\sum" in source


def test_day_ahead_notebook_is_valid_and_describes_the_24_hour_workflow():
    notebook = json.loads((ROOT / "notebooks" / "case5_day_ahead_workflow.ipynb").read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "24-hour" in source
    assert "solve_hourly_qaoa" in source
    assert "\\min" in source
    assert "real quantum processor" in source


def test_day_ahead_records_are_local_and_cover_all_hours():
    for directory in ("day_ahead", "day_ahead_local_noisy"):
        record = json.loads(
            (ROOT / "results" / directory / "case5_day_ahead.json").read_text(encoding="utf-8")
        )
        assert record["scope"]["hours"] == 24
        assert record["scope"]["real_qpu_submitted"] is False
        assert len(record["profile"]["demand_mw"]) == 24
        assert record["classical_reference"]["total_cost"] > 0.0
        assert record["hourly_qaoa"]["total_cost"] > 0.0


def test_public_tree_does_not_contain_real_qpu_submission_scripts():
    names = {path.name.lower() for path in (ROOT / "scripts").glob("*.py")}
    assert not any("real" in name or "submit" in name for name in names)
