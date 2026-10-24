from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}
FORBIDDEN_NAMES = {".env", "credentials", "secrets"}
FORBIDDEN_TERMS = (
    "stulych",
    "adskill",
    "rockapp",
    "therockapp",
)
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "GitHub token": re.compile(r"(?:ghp_|github_pat_)[0-9A-Za-z_]{30,}"),
    "AWS access key": re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
}


def main() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts) or not path.is_file():
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        relative = path.relative_to(ROOT)
        if path.name in FORBIDDEN_NAMES or any(
            part in FORBIDDEN_NAMES for part in relative.parts
        ):
            findings.append(f"forbidden file or directory: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.casefold()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                findings.append(f"client identifier '{term}' in {relative}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label} pattern in {relative}")

    if findings:
        raise SystemExit("Public-readiness check failed:\n- " + "\n- ".join(findings))
    print("Public-readiness check passed")


if __name__ == "__main__":
    main()
