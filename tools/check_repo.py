"""Pre-commit guard: refuse commits that contain data files or secrets.

Install:  cp tools/check_repo.py .git/hooks/pre-commit  (or call it from there)
Run manually: python tools/check_repo.py
Exit 1 = something staged must not be committed.
"""
import re
import subprocess
import sys

DATA_EXT = (".parquet", ".feather", ".pkl", ".pickle", ".h5")
ALLOWED_CSV = {"submissions/log.csv", "submissions/week1_public_scores.csv", "week1_output/public_scores.csv"}
TOKEN_PATTERNS = [
    re.compile(r'"key"\s*:\s*"[0-9a-f]{32}"'),           # kaggle.json
    re.compile(r"KAGGLE_KEY\s*=\s*[0-9a-f]{32}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                   # generic API keys
]


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def main():
    problems = []
    for f in staged_files():
        low = f.lower()
        if low.endswith(DATA_EXT):
            problems.append(f"data file staged: {f}")
        if low.endswith(".csv") and f not in ALLOWED_CSV and not f.startswith(("eval/", "runs/")):
            problems.append(f"csv staged outside allowed paths: {f}")
        if low.endswith("kaggle.json") or low.endswith(".env"):
            problems.append(f"secret file staged: {f}")
        try:
            text = subprocess.run(["git", "show", f":{f}"], capture_output=True, text=True,
                                  errors="ignore").stdout
        except Exception:
            continue
        for pat in TOKEN_PATTERNS:
            if pat.search(text):
                problems.append(f"token-like string in {f}")
                break
    if problems:
        print("REFUSED — fix before committing:")
        for p in problems:
            print("  -", p)
        return 1
    print("check_repo: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
