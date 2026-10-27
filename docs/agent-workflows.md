# Agent Workflows

This repository has a small always-on policy in [AGENTS.md](../AGENTS.md). Use these routing rules to keep session work predictable and avoid rediscovering the same filesystem conventions.

For branch synchronization or GitHub account problems, use [Git workflow](git-workflow.md). Branch tracking and authentication are separate concerns.

## Route the task

| Task | First action | Required follow-up |
|------|--------------|--------------------|
| Set up dependencies | Run `just setup` | Requires Python, Git and just 1.33 or newer |
| Diagnose a checkout/bot config | Run `just doctor` and `just config-check <private-config>` | Review redacted findings; verify trusted seed identity and exact DeathLink slot names |
| Create a season or import inputs | Run `just scaffold --season <season> --dry-run` with the input flags | Review the mapping, scaffold, then validate |
| Compare a renamed or normalized YAML | Run `just compare <before> <after>` | Treat any non-metadata diff as a settings change |
| Generate a seed | Run `just generate --dry-run` | Review players, installed version, APWorld drift, and command before generation |
| Host a generated seed | Run `just host <run> --dry-run` | Hosting needs network/admin authorization; update README and bot after success |
| Share seed/spoiler artifacts | Run `just publish <run> --dry-run` or `just publish-files --seed <zip> --spoiler <txt> --destination <name> --dry-run` | Publish only after ZIP, credentials, date, and destination checks pass |
| Validate or prepare a pull request | Run `just check` and `just smoke` | Run `git diff --check` and inspect the final status |
| Close or archive a session | Run `just close-session <run>` | Plan only; verify tracker/disclosure decisions before separately authorized bot shutdown |

Use `just season="2026/3. Fall" archipelago="<installed-directory>" generate --dry-run` to select a season and installation. The Windows installation default is `C:/ProgramData/Archipelago`; macOS and Linux users must supply their actual installation path. `just --list` lists the canonical recipes; scripts are their implementation sources.

## Before editing

1. Read the target season README and determine whether it is active or archived.
2. Inspect the current Git status and preserve unrelated user changes.
3. Keep player YAMLs, host settings, APWorlds, local ROMs, private runs, and revealed artifacts in their documented directories.
4. For a supplied YAML, compare the parsed settings before and after any name, description, filename, or version normalization. Do not claim a change is cosmetic without checking it.

## During editing

- Use the `just` recipes rather than direct script invocations or manual copy, rename, or move sequences.
- Use literal player aliases for active seasons. Skip `game: TBD` players during generation, but keep the placeholder YAML in the season until the game is chosen.
- Treat APWorld archives as code. Verify ZIP integrity and inspect the source or release before recommending installation or synchronization.
- Never read, print, or publish private generated spoilers, credentials, or local ROM content unless the user explicitly requests a review of a specific file and it is safe to do so.
- Do not invent room URLs, ports, seed identifiers, game settings, or release provenance. Mark unknown values as TBD and point to the owning README.

## After editing

Run the repository gate:

```powershell
just check
just smoke
git diff --check
```

If validation fails, fix the source issue or stop and report it. Never relax the validator to make a new file pass. Git mutations need the maintainer's explicit request or authorization within the task scope. Destructive cleanup or history changes need specific authorization; preserve feature branches. See [Git workflow](git-workflow.md) for account selection and [Discord bot](discord-bot.md) for the separate bot branch policy.
