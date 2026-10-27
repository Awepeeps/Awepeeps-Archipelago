"""Run Gitleaks natively or in its pinned container, with redacted output."""

import argparse
from pathlib import Path
import shutil
import subprocess

IMAGE = 'ghcr.io/gitleaks/gitleaks:v8.24.2@sha256:b5918eb91b8d2473cec722f066abb4352e4ffdc4ec9f4283ec143aba9ec9ebc4'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--container", action="store_true", help="Use the pinned read-only Docker scanner (CI).")
    args = parser.parse_args(argv)
    executable = shutil.which("docker" if args.container else "gitleaks")
    if executable is None:
        print("ERROR: Install Docker for --container or Gitleaks v8, then rerun; secret scanning was not performed.")
        return 1
    scan = ["git", str(args.repo), "--log-opts=--all", "--redact=100", "--no-banner"]
    if args.container:
        command = [executable, "run", "--rm", "--network", "none",
                   "-e", "GIT_CONFIG_COUNT=1", "-e", "GIT_CONFIG_KEY_0=safe.directory",
                   "-e", "GIT_CONFIG_VALUE_0=/repo", "-v", f"{args.repo.resolve()}:/repo:ro",
                   IMAGE, "git", "/repo", *scan[2:]]
    else:
        command = [executable, *scan]
    try:
        result = subprocess.run(command, check=False)
    except OSError:
        print("ERROR: Gitleaks could not start; secret scanning was not performed.")
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
