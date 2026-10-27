---
name: archipelago-session-workflow
description: "Set up, diagnose, generate, host, publish, or close an Awepeeps Archipelago session through just recipes; also import seasons, compare player YAMLs, and validate APWorlds."
---

# Archipelago Session Workflow

Use this skill for session lifecycle work in this repository. `just` is the canonical access point; scripts are implementation sources behind recipes. Do not invoke them directly or recreate their copy, move, or validation logic manually. Requires Python, Git and just 1.33 or newer.

## Route

- Install development dependencies: `just setup`.
- Checkout diagnosis: `just doctor`. Local bot config checks: `just config-check <private-config>`; pass `--expected-seed <trusted-name>` for exact comparison without echoing it. These checks are read-only and offline; configured identity alone does not prove a live room's identity.
- New season or bulk import: `just scaffold --season <season> --dry-run` with the selected input flags.
- Prove a YAML rename is cosmetic: `just compare <before> <after>`.
- Generation preflight: `just generate --dry-run`.
- Hosting preflight: `just host <run> --dry-run`.
- Publication preflight: `just publish <run> --dry-run`; for explicit staged paths use `just publish-files --seed <zip> --spoiler <txt> --destination <name> --dry-run`.
- Close/archive: `just close-session <run>`. Always a dry-run checklist. Verify final tracker goals and exact DeathLink slot names; obtain disclosure decisions and explicit authorization before stopping and disabling the identified bot runtime. The planner performs no network requests, shutdown, file changes or Git cleanup.
- Final gate: `just check`, followed by `just smoke` for actual-wrapper integration checks. Individual checks are `just validate`, `just compile`, and `just test`.

`just --list` shows recipes. Set `season`, `archipelago`, `input`, and `output` before the recipe name, for example `just season="2026/3. Fall" archipelago="<installed-directory>" generate --dry-run`. Windows defaults to `C:/ProgramData/Archipelago`; macOS and Linux need the actual installation path. `just secrets` requires local Gitleaks v8 and fully redacts findings. CI runs offline checks and wrapper smoke tests on Windows, macOS and Linux; real generation still needs the application and reviewed APWorlds/ROMs, while hosting needs network access and admin credentials.

Read [docs/session-workflow.md](../../../docs/session-workflow.md) for arguments, layout, and the private/revealed boundary. Read [docs/agent-workflows.md](../../../docs/agent-workflows.md) for repository-specific safety rules.

## Required behavior

1. Read the selected season README and check `git status` before editing.
2. Use a literal player alias for an active season. Keep a `game: TBD` placeholder out of generation, but do not silently delete it from the season.
3. Treat `YAML/.host.yaml` as host configuration. Never place it in `Players/` or import it as a player.
4. Preserve player settings when changing only organization. Run `just compare <before> <after>` and report any non-metadata diff.
5. Verify APWorld archives before installation or synchronization. Do not execute an unreviewed archive.
6. Keep generation work under `.secrets/hidden/`. Publish only intentionally shareable artifacts under `.secrets/revealed/`.
7. Run a dry run before each mutating lifecycle command. Do not overwrite an existing run or revealed artifact without an explicit user decision and the command's overwrite option.
8. Run `just check` after edits. If it fails, fix the underlying issue or report it; never weaken the validator.

For bot setup, derive `ExpectedSeedName` from a trusted seed artifact and configure `DailyPostConfig.DeathLinkSlots` as exact slot names. `null` means unknown; `[]` asserts no participants. Do not print tokens, passwords, channel/user IDs or private raw config. The publisher/validator enforce the binary seed credential gate; an opaque multidata entry is not evidence that a seed is safe to publish.

Do not invent room links, ports, seed identities, game settings, or release provenance. Unknown values belong in the season README as `TBD` until verified.
