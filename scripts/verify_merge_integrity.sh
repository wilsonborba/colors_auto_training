#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: run inside a git repository." >&2
  exit 1
fi

echo "[1/3] Checking unresolved merge markers in tracked files..."
if git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . ':(exclude).venv/**'; then
  echo
  echo "Error: unresolved merge markers found." >&2
  exit 1
fi

echo "[2/3] Checking Python syntax for tracked *.py files..."
python - <<'PY'
import py_compile
import subprocess
import sys

result = subprocess.run(
    ["git", "ls-files", "*.py"],
    check=True,
    capture_output=True,
    text=True,
)
files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
failed = []
for path in files:
    try:
        py_compile.compile(path, doraise=True)
    except Exception as exc:  # noqa: BLE001
        failed.append((path, str(exc)))

if failed:
    print("Syntax errors found:")
    for path, error in failed:
        print(f"- {path}: {error}")
    sys.exit(1)

print(f"OK: compiled {len(files)} Python files")
PY

echo "[3/3] Done. Merge integrity checks passed."
