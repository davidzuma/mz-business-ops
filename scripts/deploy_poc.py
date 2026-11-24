#!/usr/bin/env python3
"""Publish an MZtech PoC: private GitHub repo + Vercel production deployment.

Deterministic helper for the `poc` skill. Requires prior login:
    gh auth login        (GitHub)
    vercel login         (Vercel)
The script never logs in on the user's behalf; it stops and asks if auth
is missing.

Usage:
    python3 scripts/deploy_poc.py --dir data/pocs/<slug> [--name mztech-demo-<slug>]
                                  [--public] [--skip-github] [--skip-vercel] [--no-build]

Writes <dir>/poc.json (manifest consumed by the proposal skill) and prints
the live URL. Repos are PRIVATE by default; PoCs contain mock data only.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run(cmd, cwd=None, timeout=600, check=True):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode != 0:
        sys.stderr.write(result.stdout[-3000:] + "\n" + result.stderr[-3000:] + "\n")
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(str(c) for c in cmd)}")
    return result


def require_tool(name):
    if not shutil.which(name):
        raise RuntimeError(f"{name} CLI not found in PATH")


def check_auth(skip_github, skip_vercel):
    if not skip_github:
        require_tool("gh")
        r = run(["gh", "auth", "status", "--active"], check=False)
        if r.returncode != 0:
            raise RuntimeError("GitHub CLI not logged in. Ask the user to run: gh auth login")
    if not skip_vercel:
        require_tool("vercel")
        r = run(["vercel", "whoami"], check=False)
        if r.returncode != 0 or "Error" in r.stdout + r.stderr:
            raise RuntimeError("Vercel CLI not logged in. Ask the user to run: vercel login")


def build(dirpath, no_build):
    if no_build:
        return
    if not (dirpath / "node_modules").exists():
        run(["npm", "install", "--no-audit", "--no-fund"], cwd=dirpath, timeout=900)
    run(["npm", "run", "build"], cwd=dirpath, timeout=600)


def git_identity_ok():
    email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
    name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
    return bool(email and name)


def publish_github(dirpath, name, public):
    if not git_identity_ok():
        raise RuntimeError("git user.name/user.email not configured; ask the user to set them")
    if not (dirpath / ".git").exists():
        run(["git", "init", "-b", "main"], cwd=dirpath)
    run(["git", "add", "-A"], cwd=dirpath)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=dirpath, check=False)
    has_head = run(["git", "rev-parse", "--verify", "HEAD"], cwd=dirpath, check=False).returncode == 0
    if staged.returncode != 0 or not has_head:
        run(["git", "commit", "-m", f"PoC {name}: working prototype with mock data"], cwd=dirpath)
    else:
        print("No new changes to commit.")

    visibility = "--public" if public else "--private"
    exists = run(["gh", "repo", "view", name], check=False).returncode == 0
    if exists:
        url = run(["gh", "repo", "view", name, "--json", "url", "-q", ".url"]).stdout.strip()
        remote = run(["git", "remote", "get-url", "origin"], cwd=dirpath, check=False)
        if remote.returncode != 0:
            run(["git", "remote", "add", "origin", url], cwd=dirpath)
        branch = run(["git", "branch", "--show-current"], cwd=dirpath).stdout.strip() or "main"
        run(["git", "push", "-u", "origin", branch], cwd=dirpath)
    else:
        run(["gh", "repo", "create", name, visibility, "--source", str(dirpath), "--remote", "origin", "--push"], cwd=dirpath)
        url = run(["gh", "repo", "view", name, "--json", "url", "-q", ".url"]).stdout.strip()
    return url


def wait_live(url, attempts=10):
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def publish_vercel(dirpath, name):
    run(["vercel", "link", "--yes", "--project", name, "--cwd", str(dirpath)], timeout=300)
    r = run(["vercel", "deploy", "--prod", "--yes", "--cwd", str(dirpath)], timeout=900)
    output = r.stdout + r.stderr
    urls = re.findall(r"https://[a-zA-Z0-9.-]+\.vercel\.app", output)
    alias = f"https://{name}.vercel.app"
    production = alias if alias in urls else (urls[0] if urls else alias)
    deployment = next((u for u in urls if u != production), production)
    live = wait_live(production)
    if not live:
        print(f"WARNING: {production} did not return HTTP 200 yet; check the Vercel dashboard.")
    return production, deployment, live


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, help="PoC project directory")
    parser.add_argument("--name", help="GitHub repo + Vercel project name (default mztech-demo-<dirname>)")
    parser.add_argument("--public", action="store_true", help="Create a PUBLIC repo (default: private)")
    parser.add_argument("--skip-github", action="store_true")
    parser.add_argument("--skip-vercel", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()

    dirpath = Path(args.dir).resolve()
    if not (dirpath / "package.json").exists():
        raise RuntimeError(f"{dirpath} is not a PoC project (package.json missing)")
    name = args.name or f"mztech-demo-{dirpath.name}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,98}[a-z0-9]", name):
        raise RuntimeError(f"Invalid project name: {name} (lowercase letters, digits, hyphens)")

    check_auth(args.skip_github, args.skip_vercel)
    build(dirpath, args.no_build)

    manifest = {
        "name": name,
        "mock_data": True,
        "repo_private": not args.public,
        "deployed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not args.skip_github:
        manifest["repo_url"] = publish_github(dirpath, name, args.public)
        print(f"GitHub: {manifest['repo_url']} ({'public' if args.public else 'private'})")
    if not args.skip_vercel:
        production, deployment, live = publish_vercel(dirpath, name)
        manifest["production_url"] = production
        manifest["deployment_url"] = deployment
        manifest["live"] = live
        print(f"Live demo: {production}")

    manifest_path = dirpath / "poc.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Manifest: {manifest_path}")
    print("\nReminders: mock data only; keep the demo badge; repo is "
          f"{'PUBLIC' if args.public else 'private'}; share the URL only with intended recipients.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
