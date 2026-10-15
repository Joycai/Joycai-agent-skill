"""Create a reference-repair workspace without overwriting existing files."""
import argparse
import runpy
from pathlib import Path


def initialize(root: Path) -> None:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parent.parent / "assets"
    for name in ("references", "inputs", "edits", "generations", "design_notes"):
        (root / name).mkdir(exist_ok=True)
    rules = (assets / "AGENTS.md").read_bytes()
    agents = root / "AGENTS.md"
    if agents.exists() and agents.read_bytes() == rules:
        rules_target = agents
    else:
        rules_target = root / "REFERENCE_WORKSPACE.md" if agents.exists() else agents
    for target, content in (
        (rules_target, rules),
        (root / "references" / "INDEX.md", (assets / "INDEX.md").read_bytes()),
    ):
        try:
            with target.open("xb") as handle:
                handle.write(content)
            print(f"Created: {target}")
        except FileExistsError:
            print(f"Preserved: {target}")
    dashboard = assets.parent.parent / "reference-image-dashboard" / "scripts" / "dashboard.py"
    runpy.run_path(str(dashboard))["init"](root)
    if rules_target.name == "REFERENCE_WORKSPACE.md":
        print("Review existing AGENTS.md and merge or link REFERENCE_WORKSPACE.md without replacing project rules.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    initialize(parser.parse_args().workspace)
