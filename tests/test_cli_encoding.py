"""A consola legada não deve impedir o cálculo nem a escrita UTF-8."""
import json
import os
from pathlib import Path
import subprocess
import sys

def test_cli_cp1252_retains_pending_result_and_utf8_report(tmp_path):
    env = dict(os.environ, PYTHONIOENCODING="cp1252:strict", PYTHONUTF8="0")
    result = subprocess.run(
        [sys.executable, "-m", "punching.cli", "examples/15_bordo_343mm_594kN.json",
         "--out", str(tmp_path)],
        capture_output=True, env=env,
    )
    assert result.returncode == 1, result.stderr.decode("cp1252", errors="replace")
    assert b"\\u03b2" in result.stdout
    report = json.loads((tmp_path / "resultado.json").read_text(encoding="utf-8"))
    assert report["status"] == "BETA_PENDING"
    assert "β" in (tmp_path / "memoria.txt").read_text(encoding="utf-8")
