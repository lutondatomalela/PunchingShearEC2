"""Publica os artefactos conferidos sem substituir tags ou releases existentes."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from punching.version import VERSION

def main():
    if "-rc." not in VERSION:
        raise SystemExit("Este publicador aceita apenas release candidates.")
    repository = os.environ["GITHUB_REPOSITORY"]
    if repository != "lutondatomalela/PunchingShearEC2":
        raise SystemExit("Repositório de publicação inesperado.")
    sha = os.environ["GITHUB_SHA"]
    tag = "v" + VERSION
    artifacts = ROOT / "artifacts"
    metadata = json.loads((artifacts / "BUILD-INFO.json").read_text(encoding="utf-8"))
    assert metadata["commit"] == sha and metadata["version"] == VERSION
    assert metadata["self_test"]["status"] == "passed"
    for resource in ("releases/tags/" + tag, "git/ref/tags/" + tag):
        response = subprocess.run(["gh", "api", "repos/" + repository + "/" + resource],
                                  capture_output=True, text=True, encoding="utf-8")
        if response.returncode == 0:
            raise SystemExit("A versão já existe. Não se substituem tags nem artefactos publicados.")
        if "404" not in response.stderr:
            raise RuntimeError(response.stderr)
    assets = sorted(str(p) for p in artifacts.iterdir() if p.is_file())
    subprocess.run(["gh", "release", "create", tag, *assets, "--repo", repository,
                    "--target", sha, "--title", "PunchingShearEC2 " + VERSION,
                    "--notes-file", str(ROOT / "docs/releases" / (tag + ".md")),
                    "--prerelease", "--draft"], check=True)
    # Make the release visible only after every file has been uploaded.
    subprocess.run(["gh", "release", "edit", tag, "--repo", repository,
                    "--draft=false", "--prerelease"], check=True)

if __name__ == "__main__":
    main()
