"""Confere a integridade do código que define a base 1.15.0."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    baseline = json.loads((ROOT / "validation" / "baseline_1_15_0.json").read_text(encoding="utf-8"))
    module = ast.parse((ROOT / "punching" / "version.py").read_text(encoding="utf-8"))
    version = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets)
    )
    if version != baseline["version"]:
        print("Versão posterior: o inventário 1.15.0 conserva-se como referência histórica.")
        return 0
    expected = baseline["files_sha256"]
    failures = []
    for name, digest in expected.items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            failures.append(name)
    # Novos módulos não podem modificar silenciosamente a versão congelada.
    actual_python = {p.relative_to(ROOT).as_posix() for folder in ("punching", "tests")
                     for p in (ROOT / folder).rglob("*.py")}
    actual_python.update(p.name for p in ROOT.glob("*.py"))
    failures.extend(sorted(actual_python - set(expected)))
    if failures:
        print("A base 1.15.0 foi alterada: " + ", ".join(sorted(set(failures))), file=sys.stderr)
        return 1
    print(f"Base 1.15.0 conferida: {len(expected)} ficheiros correspondem à distribuição original.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
