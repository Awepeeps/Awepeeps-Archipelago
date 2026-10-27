# Awepeeps Archipelago

This repository organizes Archipelago multiworld configurations, setup references, and session records for the Awepeeps community.

## Guides

- [Player guide](docs/player-guide.md): community defaults, hints, and player commands.
- [Admin guide](docs/admin-guide.md): room-console commands and live-room operations.
- [Session workflow](docs/session-workflow.md): prepare, generate, host, and archive a session.
- [Discord bot](docs/discord-bot.md): operate the optional tracking bot; bot maintenance commands do not administer the Archipelago room.
- [Archipelago resources](Archipelago.md): upstream setup and community links.
- [Agent workflows](docs/agent-workflows.md) and [Git workflow](docs/git-workflow.md): repository maintenance.

## Repository layout

- `2026/<number>. <Season>/`: one folder per session season.
- `README.md` in each season: game links, player assignments, session dates, and setup notes.
- `YAML/`: player configurations and the season's `.host.yaml` generation settings.
- `APWorld/`: APWorld archives kept with the session for reference and local installation.
- `.secrets/revealed/`: spoiler logs or other files intentionally shared with the repository.
- `.secrets/hidden/`: private local files; this path is ignored.
- `.roms/`: local ROM storage; this path is ignored and must stay local.
- `.worktreeinclude`: tracked list of local-only paths (season ROM stashes, `.admin/`, `bridgeipelago/config.json`) that new worktrees need. Every path it lists is gitignored, so the file references paths without committing them.
- `.admin/`: local admin scripts and session id; this path is ignored and must stay local.
- [Archipelago resources](Archipelago.md): general setup and community links.

Spring and Summer 2026 are archived. Their historical YAMLs may retain `{player}` placeholders. New or active-season YAMLs use the literal in-game player name in `name:`.

## Preparing a session

1. Read the season README and the linked game setup guides.
2. Install each required APWorld manually into the Archipelago installation's `custom_worlds` directory. Review the source or release before installing an archive; this repository does not automatically install or trust third-party code.
3. Obtain any required game files lawfully. ROMs are never stored or linked here. Keep local copies under the season's `.roms/` directory or another local-only location.
4. Run `just generate --dry-run` with the selected season and installation to review the inputs. Actual generation copies player YAMLs from the season's `YAML/` directory without treating `.host.yaml` as a player file.
5. Use the season's `YAML/.host.yaml` for host settings. Generation copies it into the private workspace; its `Players` and `output` paths resolve there rather than in the repository.
6. Keep generated private spoilers, logs, and credentials in `.secrets/hidden/` or another ignored local directory. Move a file to `.secrets/revealed/` only when it is intentionally shareable.

For the complete create, generate, publish, and archive workflow, see [Session workflow](docs/session-workflow.md). AI agents should also follow [Agent workflows](docs/agent-workflows.md). For the optional self-hosted Discord tracking bot, see [Discord bot](docs/discord-bot.md).

### Reproducible session generation

Use `just generate` to generate a seed from one season's checked-in player YAMLs, host settings, and APWorld archives. It skips player files whose `game` is `TBD`, checks the installed Archipelago version and APWorld hashes, and writes each run to the season's ignored `.secrets/hidden/<run-id>/` directory. A run without `--run-id` uses the current date, such as `2026-09-20`.

Run a preflight first, supplying the actual installation path:

```powershell
just season="2026/3. Fall" archipelago="C:/ProgramData/Archipelago" generate --dry-run
```

After reviewing the reported players and command, omit `--dry-run` to generate. Add `--seed <number>` to select a known numeric seed, `--run-id <name>` for a memorable private output directory, and `--sync-apworlds` only after reviewing any APWorld archive that the tool reports as missing or different. Each completed run contains a `generation-manifest.json` with input hashes, the generator executable hash, and the command, plus `YYYY-MM-DD_seed.zip` and `YYYY-MM-DD_spoiler.txt` directly in the private run folder. Use `just publish <run-id> --dry-run` with the same `season` variable, then rerun without `--dry-run`, to publish those two files into the matching `.secrets/revealed/<run-id>/` folder. Treat the numeric seed as part of the run identity, not as a guarantee of byte-identical output across different Archipelago, APWorld, or runtime states.

Do not copy generated output into `.secrets/revealed/` unless the spoiler or seed is deliberately being shared with the group.

Game-specific caveats belong in the season README. For example, Fall 2026 documents the SM64 decompilation workflow and the local Crystal ROM filename expected by its host configuration.

## Common tasks

Use `just` as the canonical entry point for humans and agents. Install Python, Git and `just` 1.33 or newer, then run `just setup` from the repository root. Scripts are maintained implementation sources behind the recipes. Run `just --list` for the full set; `just check` is the pre-review gate.

```powershell
just setup
just check
just smoke
just doctor
just config-check "path with spaces/config.json"
just generate --dry-run
just host 2026-10-03_test --dry-run
just publish 2026-10-03_test --dry-run
just close-session 2026-10-03_test
just secrets
```

`just validate`, `just compile`, and `just test` run the individual checks. `just scaffold` imports inputs, `just compare <before> <after>` compares YAMLs, and `just publish-files` accepts explicit seed/spoiler paths. `just secrets` requires Gitleaks v8; all findings are redacted. `just close-session` always produces a read-only plan.

The `generate` recipe reads the selected season's YAMLs and writes to its `.secrets/hidden` directory by default. Override `season`, `archipelago`, `input`, and `output` before the recipe name. The installation defaults to `C:/ProgramData/Archipelago` on Windows; macOS and Linux users must supply their actual installation path. For example:

```powershell
just season="2026/4. Winter" archipelago="/path/to/Archipelago" input="2026/4. Winter/YAML" output="2026/4. Winter/.secrets/hidden" generate --dry-run
just generate --run-id 2026-10-03_test --dry-run
just publish 2026-10-03_test --dry-run
```

## Validation

Set up development dependencies once, then run the checks from the repository root:

```powershell
just setup
just check
just smoke
```

The validator checks season structure, YAML parsing, active player names, duplicate names, APWorld ZIP integrity, local Markdown links, ignore rules, credentials, and tracked or non-ignored files with common ROM extensions. GitHub Actions runs checks and actual-recipe smoke tests on Windows, macOS and Linux, plus a redacted Git-history secret scan. Smoke tests use isolated argument-forwarding fixtures and CLI help checks; CI does not generate live games or host rooms. Real generation requires the installed Archipelago application and reviewed APWorlds/ROMs, and hosting needs network access and admin credentials.

## Contribution rules

- Keep changes scoped to the relevant season and preserve archived session history unless a maintainer explicitly requests an archive correction.
- Use `player_game_vN.yaml` filenames and literal player aliases for active sessions.
- Never commit ROMs, ROM download links, private secrets, generated credentials, or unreviewed generated output.
- Run the validator before asking for review. The pull-request template records the remaining manual checks.
- Read [AGENTS.md](AGENTS.md) before making repository changes with an AI coding agent.
