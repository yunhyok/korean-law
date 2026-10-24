"""Install the self-contained skill; refuse to overwrite a different existing copy."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile


def files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).digest()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        and not any(part.endswith(".egg-info") for part in path.parts)
    }


def install(source: Path, destination: Path, dry_run: bool = False) -> str:
    if destination.exists():
        if files(source) == files(destination):
            return f"Already installed: {destination}"
        raise FileExistsError(f"Existing different skill: {destination}. Back it up or move it before installing.")
    if dry_run:
        return f"Would install: {destination}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".korean-law-", dir=destination.parent) as staging:
        staged = Path(staging) / "korean-law"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
        if files(source) != files(staged):
            raise OSError("Skill copy verification failed")
        staged.rename(destination)
    return f"Installed and byte-verified: {destination}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=["codex", "claude"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "skills" / "korean-law"
    base = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") if args.client == "codex" else Path.home() / ".claude"
    try:
        print(install(source, base / "skills" / "korean-law", args.dry_run))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
