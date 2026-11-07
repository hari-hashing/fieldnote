#!/usr/bin/env python3
"""Assemble only the public static-site payload for GitHub Pages."""
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for name in ("index.html", "README.md", "LICENSE"):
    if (ROOT / name).exists():
        shutil.copy2(ROOT / name, OUT / name)
for name in ("assets", "docs"):
    src = ROOT / name
    if src.exists():
        shutil.copytree(src, OUT / name)
# Deliberately publish only the data files used by the UI, not ingestion scripts or credentials/config.
data_out = OUT / "data"
data_out.mkdir()
for name in ("taxonomy.json", "papers.json", "opportunities.json", "manifest.json"):
    shutil.copy2(ROOT / "data" / name, data_out / name)
shutil.copytree(ROOT / "data" / "archives", data_out / "archives")
(OUT / ".nojekyll").write_text("", encoding="utf-8")
print(f"Built static site at {OUT}")
