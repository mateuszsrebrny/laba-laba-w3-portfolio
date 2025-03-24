import subprocess
from pathlib import Path

out_file = Path(__file__).resolve().parent.parent / "commit.txt"

with out_file.open("w") as f:
    commit = subprocess.check_output(["git", "log", "-1", "--format=%h (%cd)", "--date=short"]).decode().strip()
    f.write(commit)
