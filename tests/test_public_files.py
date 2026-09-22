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


def test_public_tree_does_not_contain_real_qpu_submission_scripts():
    names = {path.name.lower() for path in (ROOT / "scripts").glob("*.py")}
    assert not any("real" in name or "submit" in name for name in names)
