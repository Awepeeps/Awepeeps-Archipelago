"""Produce a read-only session closure checklist. No execution mode is provided."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def closure_plan(repo: Path, season: str, run: str) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run) or run in (".", ".."):
        raise ValueError("--run must be a single run directory name using letters, digits, dots, underscores or hyphens.")
    root = repo.resolve()
    target = (root / season).resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("--season must select a season within --repo.")
    if not (target / "README.md").is_file():
        raise ValueError("Selected season README is missing; check --repo and --season.")
    private = target / ".secrets" / "hidden" / run
    revealed = target / ".secrets" / "revealed" / run
    if any(path.is_symlink() for path in (target, private, revealed)) or not private.resolve().is_relative_to(target) or not revealed.resolve().is_relative_to(target):
        raise ValueError("Run paths must remain inside the selected season; inspect symlinks locally.")
    return [
        "Final tracker verification: pending. Independently check the intended seed and every player's final status; location totals alone do not prove goals. Network access needs explicit user opt-in and is not performed by this tool.",
        "Verify DeathLink completion separately against DailyPostConfig.DeathLinkSlots; null means unknown. Record a dated final summary without credentials or private identifiers.",
        f"Private run: {'present' if private.is_dir() else 'MISSING; locate trusted staged artifacts before publication'}. Revealed archive: {'already present; review contents and avoid overwrite' if revealed.exists() else 'not present'}.",
        "Archive: obtain the group's spoiler disclosure decision, then run the publisher dry run for the selected season/run. Review ZIP integrity, embedded credentials, ROM checks, manifest hashes, destination and overwrite handling before separately authorized publication.",
        "Documentation: update the season README status and final room/session links after verification; preserve historical YAML settings and table structure. Keep private run sources until retained artifacts are verified.",
        "Bot shutdown: after explicit authorization for the identified runtime, stop AND disable its service (or equivalent container restart policy); verify stopped and disabled so it stays offline after reboot. This planner does not execute shutdown commands.",
        "Final review: run just check and git diff --check; review status. Git staging, commit, push and cleanup require their own explicit authorization; preserve feature branches and user work.",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--season", required=True)
    parser.add_argument("--run", required=True, help="Private run directory name, not an arbitrary path.")
    parser.add_argument("--dry-run", action="store_true", required=True, help="Required acknowledgement: plan only, no execution mode.")
    args = parser.parse_args(argv)
    try:
        plan = closure_plan(args.repo, args.season, args.run)
    except (OSError, ValueError):
        print("ERROR: Cannot plan closure; ensure --season has a README inside --repo and --run is a simple directory name with no escaping symlinks.")
        return 1
    print("Session closure plan only; nothing was changed and no network request was made.")
    for index, item in enumerate(plan, 1):
        print(f"{index}. {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
