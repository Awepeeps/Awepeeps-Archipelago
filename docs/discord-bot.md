# Discord Tracking Bot

A session may run a self-hosted Discord bot so the group can follow check,
DeathLink, and hint activity in a channel. The supported bot is
[bridgeipelago](https://github.com/Quasky/bridgeipelago) (v3.0.0 or newer),
which connects to the room as a **spectator slot**. This document is the
reusable procedure; the season README records the specific bot slot for that
session.

## Spectator slot model

- The bot input uses `game: Archipelago`. That game maps to Archipelago's hidden
  GenericWorld, whose `generate_early` marks the player `SlotType.spectator`.
  The slot holds no items or locations and cannot affect the multiworld.
- The YAML `name` must equal the bot's `ArchipelagoBotSlot` in `config.json`.
- A dedicated spectator slot is preferred. Pointing the bot at a real player's
  slot works but makes it consume that player's item stream, so avoid it.

## Bot input

Add one file to the season's `YAML/` directory, named
`<BotName>_Archipelago_vN.yaml` so it satisfies the repository's
`player_game_vN.yaml` rule. For example:

```yaml
name: Bridgeipelago
game: Archipelago
description: Bridgeipelago Discord tracking bot (spectator slot)
Archipelago: {}
```

The slot must exist in the generated multiworld, so add this input **before**
generation. It is a normal season input and is included by
`scripts/generate_session.py`; it is not a playable player, so do not add it to
the season's player table.

## Secrets and layout

- `config.json` contains the Discord bot token and the room password. Never
  commit it, the token, the password, or the bot's data folders.
- Keep the bridgeipelago clone and its `config.json` **outside** this
  repository. If it must live here, put it under the ignored
  `.secrets/hidden/` path.
- The bot writes `logs/`, `RegistrationData/`, `ItemQueue/`, and `ArchData/`
  relative to its working directory, keyed by `UniqueID`. Run it from its own
  directory so those folders stay together.

## Host on WSL2

Native Windows is unsupported by bridgeipelago v3; use WSL2 (or Docker).

1. Install WSL2/Ubuntu if needed: `wsl --install -d Ubuntu` in an admin
   PowerShell, then reboot and set the Linux user.
2. Install prerequisites (skip any already present):
   `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip`
3. Clone the pinned release and install dependencies:
   ```bash
   git clone https://github.com/Quasky/bridgeipelago.git ~/bridgeipelago
   cd ~/bridgeipelago
   git checkout live-v3.0.0
   python3 -m venv .venv
   ./.venv/bin/python -m pip install --upgrade pip
   ./.venv/bin/python -m pip install -r requirements.txt
   ./.venv/bin/python -m pip install "websockets<14"   # newer versions break the receive loop
   ```
4. Create `config.json` from the shipped template, apply the `LanguageFile`
   fix, and fill the values (see Configuration).
5. Run it interactively, or install it as a WSL service (below):
   `./.venv/bin/python bridgeipelago.py config.json`

The clone lives outside this repository, so `config.json` and the data folders
never enter Git. If a dependency will not build on the installed Python,
install Python 3.12 and recreate the venv with it.

Verified environment: WSL2 Ubuntu, Python 3.14, git 2.53, bridgeipelago
`live-v3.0.0` (commit `a3e4e03`).

## Run as a WSL service

With systemd enabled in WSL, run the bot as a user service so it starts on boot
and restarts on failure.

Create `~/.config/systemd/user/bridgeipelago.service` (replace `<user>` with the
Linux username):

```ini
[Unit]
Description=Bridgeipelago Discord bot for Archipelago
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/<user>/bridgeipelago
ExecStart=/home/<user>/bridgeipelago/.venv/bin/python -u /home/<user>/bridgeipelago/bridgeipelago.py config.json
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/<user>/bridgeipelago/bot.out
StandardError=append:/home/<user>/bridgeipelago/bot.out

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now bridgeipelago
loginctl enable-linger "$USER"   # start on boot without an active login
systemctl --user status bridgeipelago
```

Logs go to `journalctl --user -u bridgeipelago -f` and the appended
`~/bridgeipelago/bot.out`. Stop or restart with
`systemctl --user stop|restart bridgeipelago`.

## Docker alternative

Install Docker Desktop with WSL integration and run `docker compose up -d` from
the clone. `docker-compose.yaml` mounts the four data folders; if you change the
data paths in `AdvancedConfig`, update the mounts to match.

## Configuration

Start from this repository's
[bridgeipelago config template](bridgeipelago.config.template.json), which
pre-sets the recommended defaults, or from the `config.json.template` that ships
with the release you clone and apply the same values. The template and the code
have drifted historically, so do not hand-copy keys from the README.

Recommended defaults: `ItemFilterConfig.BotItemFilterLevel` `1` (progression +
useful in the channel feed), `ItemFilterConfig.BotItemSpoilTraps` `false`,
`AdvancedConfig.SnoozeCompletedGames` `true` (skip checks from finished games),
and `MetaConfig.LanguageFile` `en`.

| Section | Keys to set |
|---------|-------------|
| `DiscordConfig` | `DiscordToken`, `DiscordBroadcastChannel`, `DiscordAlertUserID`, `DiscordDebugChannel` |
| `ArchipelagoConfig` | `ArchipelagoServer` (`wss://archipelago.gg`), `ArchipelagoPort`, `ArchipelagoPassword`, `ArchipelagoBotSlot` (must equal the YAML `name`), `ArchipelagoTrackerURL`, `ArchipelagoServerURL`, `UniqueID` |
| `ItemFilterConfig` | `BotItemSpoilTraps`, `BotItemFilterLevel` |
| `RelayConfig` | AP-to-Discord relay toggles; leave `SendOwnSlotMessages` off for a dedicated slot |
| `DrawbridgeConfig` | `DiscordBridgeEnabled` to relay Discord chat back to the room |
| `MetaConfig` | `FlavorDeathlink`, and `LanguageFile` (see gotcha) |
| `AdvancedConfig` | `QueueOverclock`, `SnoozeCompletedGames`, `SelfHostNoWeb`, and the four data directories |

**LanguageFile gotcha:** the v3.0.0 `config.json.template` omits
`MetaConfig.LanguageFile`, but the code reads it, so some messages render as
`LANG_KEY_ERROR`. After copying the template, add the key:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("config.json")
c = json.loads(p.read_text())
c.setdefault("MetaConfig", {})["LanguageFile"] = "en"
p.write_text(json.dumps(c, indent=4) + "\n")
PY
```

`ArchipelagoServerURL` and `ArchipelagoTrackerURL` must be the real room URLs;
the bot polls room status to follow port changes, and wrong URLs break that.

## Discord application

1. Discord Developer Portal -> New Application (or reuse an existing bot).
2. Installation -> Installation Contexts: enable `Guild Install`. In
   Default Install Settings (Guild Install):
   - Scopes: `applications.commands` and `bot`
   - Permissions: `View Channels`, `Send Messages`, `Read Message History`,
     `Embed Links`, `Attach Files`
   Save. The `bot` scope is what makes Discord create the bot's managed role.
3. Bot tab: enable `Public Bot` and `Message Content Intent` (bridgeipelago
   reads `$` commands from message content); copy the token.
4. Invite the bot with the install link. Discord creates an
   integration-managed role named after the bot with the selected permissions
   and auto-applies it on every server the bot joins. A managed role cannot be
   edited or assigned manually; the server owner only positions it.
5. Create a broadcast channel and a private debug channel; enable Developer
   Mode and copy both channel IDs and your own user ID.

To give an already-added bot a managed role, add the `bot` scope to the default
install settings and re-add the bot (kick it, then invite it again). Re-adding
does not change the token.

**Channel permissions:** the bot's managed role needs `View Channel` and
`Send Messages` in both the broadcast and debug channels. A staff-only channel
that denies `Send Messages` makes the bot's `on_ready` fail with
`403 Missing Access`, so use a bot-friendly debug channel (for example a
`#bot-commands`) or add a channel overwrite for the managed role.

## Registration and commands

Commands run in the broadcast channel (the bot only reads messages there) and
are case-sensitive. `$register` links your Discord account to a slot; the other
player commands act on your registered slot(s). Upstream reference:
[bridgeipelago commands](https://github.com/Quasky/bridgeipelago#commands).

Player commands:

| Command | Effect |
|---------|--------|
| `$register <slot>` | Link your Discord account to an Archipelago slot |
| `$listreg` | DM the slots you are registered for |
| `$clearreg` | Remove all of your registrations |
| `$ketchmeup <2\|1\|0>` | DM checks you missed: `2` progression, `1` +useful, `0` +normal |
| `$groupcheck <slot>` | DM all queued checks for a slot (group games) |
| `$hints` | DM hinted items for your registered slots |
| `$hint <slot> \| <item>` | Request a hint; the result is relayed to the channel |
| `$deathcount` | Post the current DeathLink tally |
| `$checkcount` | Post the current check counts |
| `$checkgraph` | Post a check-progress graph image |

Admin commands:

| Command | Effect |
|---------|--------|
| `$hello`, `$iloveyou` | Trivial responses |
| `$reloadtracker`, `$reloaddiscord` | Reload the tracker or the Discord client |
| `$setconfig <key> <value>` | Change a `config.json` value (`ArchipelagoPort`, URLs, `UniqueID`) |
| `$ArchInfo` | Debug details (only when `DebugMode` is on) |

## Notifications

There are two separate paths with separate filters:

- **Channel feed (not per-user, not opt-in).** Every check and item event is
  posted to the broadcast channel. The host sets the level in `config.json`
  with `ItemFilterConfig.BotItemFilterLevel`: `2` progression only, `1`
  progression + useful, `0` progression + useful + normal (traps only when
  `BotItemSpoilTraps` is true). `AdvancedConfig.SnoozeCompletedGames` skips
  checks from games that have already finished. Players cannot change this.
- **Personal DMs (opt-in).** `$register <slot>` links a Discord account to a
  slot and starts queuing items **other players send to you**; your own finds
  are not queued (you see those in-game). Pull them with `$ketchmeup <2|1|0>`,
  which chooses the level per request. `$hints` DMs hinted items and
  `$groupcheck <slot>` DMs all queued items for a slot. There is no automatic
  push DM.

The bot identifies players by slot, so a second game on the same account is
treated as someone else's items. Upstream: [bridgeipelago functionality](https://github.com/Quasky/bridgeipelago#functionality).

## DeathLink

DeathLink is a per-game Archipelago option. Only games with it enabled send and
receive deaths; the bot is a passive spectator that receives every DeathLink
broadcast (it never sends one).

When one arrives, and `RelayConfig.DeathlinkMessages` is true, the bot posts to
the broadcast channel:

> **Deathlink!** Received from **&lt;player&gt;**
> *Cause:* &lt;cause&gt;

`MetaConfig.FlavorDeathlink` replaces the "Received from" line with random flavor
from the project's `modules/DeathlinkFlavor.py`. Every received death is also
appended to `logs/<UniqueID>/DeathLog.txt`, which backs `$deathcount` and
`$deathgraph`. `DeathlinkLottery` is unused.

## Room or port changes

Use `$setconfig <key> <value>` for `ArchipelagoPort`,
`ArchipelagoTrackerURL`, `ArchipelagoServerURL`, and `UniqueID`, then
`$reloadtracker` and `$reloaddiscord`. Bring the room up first so the bot can
connect during the reload.

## Verify

- `python scripts/validate_repo.py` passes with the bot input in place.
- `python scripts/generate_session.py --season <season> --archipelago <install> --dry-run`
  lists the bot slot among the players (preflight only).
- The bot connects and posts a real check to the broadcast channel.

## Troubleshooting

- **The bot connects and posts its startup message but never relays checks,
  chat, or DeathLink.** The unpinned `websockets` dependency resolved to 16+;
  bridgeipelago v3.0.0 calls `websockets.connect()` without a context manager,
  which newer versions no longer support. Install `websockets<14` in the venv
  (13.1 is verified) and restart.
- **Relays still do not fire on Python 3.14.** The bot targets Python 3.12 (its
  Dockerfile). If the loop tasks misbehave on a newer interpreter, build the
  venv with Python 3.12 or use the Docker image.

## Trust

bridgeipelago is a third-party application and has no license. Review the
release and source before running it, and never place its credentials in this
repository.
