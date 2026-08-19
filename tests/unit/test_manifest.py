"""Manifest load and seed resolution tests (no engine required)."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.manifest_utils import load_manifest, resolve_seeds


def test_load_baseline_manifest():
    path = Path("experiments/manifests/v2_vs_v0_baseline.json")
    manifest = load_manifest(path)
    seeds = resolve_seeds(manifest)
    assert len(seeds) == 5
    assert manifest["bot_a"] == "montecarlo"


def test_seed_list_file(tmp_path):
    seed_file = tmp_path / "seeds.txt"
    seed_file.write_text("10\n20\n30\n", encoding="utf-8")
    manifest = {"seed_list_file": str(seed_file)}
    assert resolve_seeds(manifest) == [10, 20, 30]
