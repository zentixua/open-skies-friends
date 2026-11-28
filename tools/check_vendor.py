#!/usr/bin/env python3
"""Own builds of third-party mods (vendor/, AGENTS.md) stay reachable and match what the pack installs.

A metafile that links this repository's raw.githubusercontent.com by commit must name a commit in the checked
history (a squash merge would leave it only in refs/pull/*), the file must exist at that commit under vendor/, equal
the working tree's copy, and match the metafile's hash; such a mod is pinned and has no update source.

Usage: python3 tools/check_vendor.py [repository root, default: .]   (needs the full history: fetch-depth 0)
"""
import hashlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

RAW = re.compile(r"https://raw\.githubusercontent\.com/zentixua/open-skies-friends/([0-9a-f]{40})/(vendor/.+)")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


def problems(root: Path):
    for f in sorted((root / "pack").rglob("*.pw.toml")):
        meta = tomllib.loads(f.read_text(encoding="utf-8"))
        match = RAW.fullmatch(meta.get("download", {}).get("url", ""))
        if not match:
            continue
        rel = f.relative_to(root)
        commit, path = match.groups()
        if git(root, "merge-base", "--is-ancestor", commit, "HEAD").returncode != 0:
            yield f"{rel}: commit {commit} is not in this branch's history (merge vendor PRs with a merge commit)"
            continue
        blob = git(root, "show", f"{commit}:{path}")
        if blob.returncode != 0:
            yield f"{rel}: {path} does not exist at {commit}"
            continue
        local = root / path
        if not local.is_file() or local.read_bytes() != blob.stdout:
            yield f"{rel}: {path} in the working tree differs from {commit} (a new build needs a new file name)"
        dl = meta["download"]
        if hashlib.new(dl["hash-format"], blob.stdout).hexdigest() != dl["hash"]:
            yield f"{rel}: {dl['hash-format']} of {path} at {commit} differs from the metafile"
        if not meta.get("pin") or "update" in meta:
            yield f"{rel}: an own build needs pin = true and no [update] section"


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    found = list(problems(root))
    for p in found:
        print(p)
    if found:
        sys.exit(f"{len(found)} problem(s)")
    print("own builds: linked by a commit in history, files and hashes match")


if __name__ == "__main__":
    main()
