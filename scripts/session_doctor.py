"""Read-only local session checks; never display private config values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def git_read(root: Path, *args: str) -> str:
    """Capture diagnostics, including stderr, without leaking remote credentials."""
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(root), *args],
            capture_output=True, text=True, check=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("Git inspection failed; check Git installation and repository access locally.") from None
    return result.stdout.strip()


def placeholder(value: object) -> bool:
    return not isinstance(value, str) or not value.strip() or "<" in value or ">" in value


def validate_config(path: Path, expected_seed: str | None = None) -> tuple[list[str], list[str]]:
    """Return fixed messages only: no JSON values, filenames or parser exceptions."""
    errors: list[str] = []
    notes: list[str] = []
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return ["Bot config is missing, unreadable, or invalid JSON; check --bot-config locally."], notes
    if not isinstance(config, dict):
        return ["Bot config must be a JSON object."], notes
    sections = {}
    for name in ("DiscordConfig", "ArchipelagoConfig", "DailyPostConfig", "MetaConfig"):
        section = config.get(name)
        if not isinstance(section, dict):
            errors.append(f"{name} must be an object.")
            section = {}
        sections[name] = section
    discord = sections["DiscordConfig"]
    for key in ("DiscordToken", "DiscordBroadcastChannel", "DiscordDebugChannel"):
        value = discord.get(key)
        if placeholder(value) or (key != "DiscordToken" and not value.isdecimal()):
            errors.append(f"DiscordConfig.{key} needs a configured value of the documented type.")
    ap = sections["ArchipelagoConfig"]
    for key in ("ArchipelagoBotSlot", "UniqueID", "ExpectedSeedName"):
        if placeholder(ap.get(key)):
            errors.append(f"ArchipelagoConfig.{key} must be set from this session's trusted inputs.")
    password = ap.get("ArchipelagoPassword")
    if not isinstance(password, str) or "<" in password or ">" in password:
        errors.append("ArchipelagoConfig.ArchipelagoPassword must be a string; replace template placeholders (empty is allowed).")
    if expected_seed is not None and (not isinstance(ap.get("ExpectedSeedName"), str) or ap["ExpectedSeedName"].strip() != expected_seed.strip()):
        errors.append("ExpectedSeedName does not match the supplied trusted seed identity.")
    elif not placeholder(ap.get("ExpectedSeedName")) and expected_seed is None:
        notes.append("ExpectedSeedName is configured; independently compare it to the trusted AP_<seed_name>.archipelago filename, or pass --expected-seed.")
    port = ap.get("ArchipelagoPort")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        errors.append("ArchipelagoConfig.ArchipelagoPort must be an integer from 1 to 65535.")
    for key, kind in (("ArchipelagoServerURL", "room"), ("ArchipelagoTrackerURL", "tracker")):
        value = ap.get(key)
        try:
            url = urlsplit(value) if isinstance(value, str) else None
            valid = url is not None and url.scheme == "https" and bool(url.hostname) and not url.username and not url.password and not url.query and not url.fragment
            parts = url.path.strip("/").split("/") if url else []
            valid = valid and len(parts) == 2 and parts[0] == kind and not placeholder(parts[1])
        except ValueError:
            valid = False
        if not valid:
            errors.append(f"ArchipelagoConfig.{key} must be a configured HTTPS {kind} URL without credentials or query parameters.")
    daily = sections["DailyPostConfig"]
    slots = daily.get("DeathLinkSlots")
    if slots is None:
        notes.append("DeathLinkSlots is unknown (null); set exact participating slot names before treating DeathLink games as complete. Use [] only if none participate.")
    elif not isinstance(slots, list) or any(not isinstance(slot, str) or not slot.strip() for slot in slots):
        errors.append("DailyPostConfig.DeathLinkSlots must be null or a list of exact non-empty slot names.")
    elif len(slots) != len(set(slots)):
        errors.append("DailyPostConfig.DeathLinkSlots contains duplicate slot names.")
    if not isinstance(daily.get("Enabled", False), bool):
        errors.append("DailyPostConfig.Enabled must be true or false.")
    language = sections["MetaConfig"].get("LanguageFile")
    if language is not None and (not isinstance(language, str) or not language.strip()):
        errors.append("MetaConfig.LanguageFile must be a non-empty string when configured.")
    return errors, notes


def inspect_git(root: Path) -> list[str]:
    git_read(root, "rev-parse", "--show-toplevel")
    status = git_read(root, "status", "--porcelain=v1", "--untracked-files=normal")
    branch = git_read(root, "branch", "--show-current")
    remotes = git_read(root, "remote").splitlines()
    worktrees = git_read(root, "worktree", "list", "--porcelain")
    # Report counts rather than URLs, file names, or config-derived identities.
    return [
        f"Git: {'branch checkout' if branch else 'DETACHED HEAD; select the intended branch before editing'}.",
        f"Git status: {len(status.splitlines()) if status else 0} changed/untracked entries; preserve unrelated changes.",
        f"Git remotes: {len(remotes)} configured; inspect account permissions locally before an authorized push.",
        f"Git worktrees: {sum(line.startswith('worktree ') for line in worktrees.splitlines())}; confirm the intended checkout before editing.",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--bot-config", type=Path, help="Private JSON config; relative paths resolve against --repo.")
    parser.add_argument("--expected-seed", help="Trusted seed identity for exact comparison; never echoed.")
    parser.add_argument("--config-only", action="store_true", help="Check config only; requires --bot-config.")
    args = parser.parse_args(argv)
    if args.config_only and args.bot_config is None:
        parser.error("--config-only requires --bot-config")
    if args.expected_seed is not None and args.bot_config is None:
        parser.error("--expected-seed requires --bot-config")
    errors = []
    print("Read-only local checks; no network requests or runtime changes.")
    if not args.config_only:
        try:
            for message in inspect_git(args.repo):
                print(message)
        except ValueError as error:
            errors.append(str(error))
    if args.bot_config is not None:
        path = args.bot_config if args.bot_config.is_absolute() else args.repo / args.bot_config
        config_errors, notes = validate_config(path, args.expected_seed)
        errors.extend(config_errors)
        for note in notes:
            print("NOTE: " + note)
        if not config_errors:
            print("Bot config: local shape checks passed; credentials and live room identity are not authenticated.")
    else:
        print("NOTE: Bot config not checked; pass --bot-config to validate local session settings.")
    for error in errors:
        print("ERROR: " + error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
