"""Compila e ensaia o executável Windows; não publica ficheiros."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from punching.version import VERSION

def main():
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("A distribuição Windows x64 deve ser compilada em Windows x64.")
    from PIL import Image, ImageDraw
    work = ROOT / "build/windows"
    work.mkdir(parents=True, exist_ok=True)
    # Identidade gráfica da aplicação: pilar e perímetro, sem recursos externos.
    icon = Image.new("RGB", (256, 256), "#14283f")
    draw = ImageDraw.Draw(icon)
    draw.ellipse((25, 25, 231, 231), outline="#68acf4", width=10)
    draw.line((30, 200, 226, 200), fill="#68acf4", width=10)
    draw.rectangle((98, 82, 158, 173), fill="#e5f0ff")
    icon.save(work / "app.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    version_resource = """VSVersionInfo(
  ffi=FixedFileInfo(filevers=(1,15,1,1), prodvers=(1,15,1,1), mask=0x3f,
                   flags=0x2, OS=0x40004, fileType=0x1, subtype=0, date=(0,0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'Lutonda Tomalela'),
    StringStruct('FileDescription', 'PunchingShearEC2 - Verificação ao punçoamento'),
    StringStruct('FileVersion', '%s'),
    StringStruct('InternalName', 'PunchingShearEC2'),
    StringStruct('OriginalFilename', 'PunchingShearEC2.exe'),
    StringStruct('ProductName', 'PunchingShearEC2'),
    StringStruct('ProductVersion', '%s')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
""" % (VERSION, VERSION)
    (work / "version.txt").write_text(version_resource, encoding="utf-8")
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--noupx", "--name", "PunchingShearEC2", "--paths", str(ROOT),
        "--icon", str(work / "app.ico"), "--version-file", str(work / "version.txt"),
        "--add-data", str(ROOT / "examples") + ":examples", "--collect-data", "reportlab",
        "--specpath", str(work), "--workpath", str(work / "temp"),
        "--distpath", str(ROOT / "dist"), str(ROOT / "desktop.py")
    ], cwd=ROOT, check=True)
    exe = ROOT / "dist/PunchingShearEC2.exe"
    # Run from a different directory with accented names: no project resources
    # may be resolved through the working directory of the build.
    with tempfile.TemporaryDirectory(prefix="Ensaio ligação ") as folder:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        run = subprocess.run([str(exe), "--self-test", folder], cwd=folder, env=env, timeout=120)
        evidence_path = Path(folder) / "self-test.json"
        if not evidence_path.exists():
            raise RuntimeError("O executável não produziu evidência do ensaio.")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        print(json.dumps(evidence, ensure_ascii=True))
        if run.returncode != 0 or evidence["status"] != "passed":
            raise RuntimeError("O ensaio do executável falhou.")
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    name = "PunchingShearEC2-" + VERSION + "-Windows-x64"
    shutil.copy2(exe, artifacts / (name + ".exe"))
    commit = os.environ.get("GITHUB_SHA") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = {
        "product": "PunchingShearEC2", "version": VERSION, "channel": "release-candidate",
        "commit": commit, "platform": "Windows x64", "python": platform.python_version(),
        "packages": {p: importlib.metadata.version(p) for p in ("pyinstaller", "reportlab", "openpyxl", "pillow")},
        "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "self_test": evidence, "code_signed": False,
        "manual_visual_review": "pending",
    }
    (artifacts / "BUILD-INFO.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    notices = work / "licenses"
    notices.mkdir(exist_ok=True)
    for package in ("reportlab", "openpyxl", "pillow", "et_xmlfile", "pyinstaller"):
        distribution = importlib.metadata.distribution(package)
        for entry in distribution.files or []:
            if any(word in str(entry).lower() for word in ("license", "copying", "notice")):
                source = Path(distribution.locate_file(entry))
                if source.is_file() and source.stat().st_size < 500000:
                    dest = notices / package / Path(str(entry)).name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.exists():
        shutil.copy2(python_license, notices / "Python-LICENSE.txt")
    for folder in (Path(sys.base_prefix) / "tcl").glob("*"):
        for license_file in folder.glob("license*"):
            if license_file.is_file():
                shutil.copy2(license_file, notices / (folder.name + "-" + license_file.name))
    with zipfile.ZipFile(artifacts / (name + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(exe, "PunchingShearEC2.exe")
        z.write(ROOT / "LICENSE", "LICENSE")
        z.write(ROOT / "docs/INSTALACAO_WINDOWS.md", "LEIA-ME.md")
        z.write(artifacts / "BUILD-INFO.json", "BUILD-INFO.json")
        for p in ROOT.glob("*.md"):
            z.write(p, p.name)
        for base in ("examples", "docs"):
            for p in (ROOT / base).rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(ROOT).as_posix())
        for p in notices.rglob("*"):
            if p.is_file():
                z.write(p, "licenses/" + p.relative_to(notices).as_posix())
    source_name = "PunchingShearEC2-" + VERSION + "-source.zip"
    subprocess.run(["git", "archive", "--format=zip", "--prefix=PunchingShearEC2/",
                    "--output=" + str(artifacts / source_name), commit], cwd=ROOT, check=True)
    assets = sorted(p for p in artifacts.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
    (artifacts / "SHA256SUMS.txt").write_text("".join(
        hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in assets
    ), encoding="ascii")
    print("Windows build and executable self-test passed.")

if __name__ == "__main__":
    main()
