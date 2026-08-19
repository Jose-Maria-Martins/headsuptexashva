"""Experiment manifest loading, provenance, and replay helpers."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def git_revision(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = subprocess.call(["git", "diff", "--quiet"], cwd=root) != 0
        return {"commit": commit, "dirty": dirty}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"commit": None, "dirty": None}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def runtime_metadata() -> dict[str, Any]:
    meta: dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        import pybind11

        meta["pybind11_version"] = pybind11.__version__
    except ImportError:
        meta["pybind11_version"] = None
    return meta


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    data["_manifest_path"] = str(manifest_path.resolve())
    return data


def resolve_seeds(manifest: dict[str, Any]) -> list[int]:
    if "seeds" in manifest and manifest["seeds"]:
        return [int(s) for s in manifest["seeds"]]
    if "seed_list_file" in manifest:
        seed_path = Path(manifest["seed_list_file"])
        if not seed_path.is_absolute():
            seed_path = repo_root() / seed_path
        with open(seed_path, encoding="utf-8") as f:
            return [int(line.strip()) for line in f if line.strip()]
    raise ValueError("Manifest must include 'seeds' or 'seed_list_file'")


def build_provenance(manifest: dict[str, Any], output_paths: list[Path] | None = None) -> dict[str, Any]:
    root = repo_root()
    prov = {
        "manifest": manifest.get("_manifest_path"),
        "manifest_name": manifest.get("name"),
        "git": git_revision(root),
        "runtime": runtime_metadata(),
        "config": {k: manifest[k] for k in manifest if not k.startswith("_") and k != "schema_version"},
    }
    if output_paths:
        prov["output_hashes"] = {str(p): file_sha256(p) for p in output_paths if p.exists()}
    return prov


def default_run_dir(name: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = repo_root() / "experiments" / "runs" / f"{name}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
