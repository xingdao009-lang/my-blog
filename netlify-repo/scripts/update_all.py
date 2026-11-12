import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

steps = [
    ("Update public news", BASE_DIR / "scripts" / "update_news.py"),
    ("Sync site profile data", BASE_DIR / "scripts" / "build_profile.py"),
    ("Build published articles", BASE_DIR / "scripts" / "build_articles.py"),
]

for label, script in steps:
    print("\n== {} ==".format(label), flush=True)
    result = subprocess.run([PYTHON, str(script)], cwd=str(BASE_DIR))
    if result.returncode != 0:
        print("Step failed: {} (exit {})".format(script.name, result.returncode), flush=True)
        sys.exit(result.returncode)

