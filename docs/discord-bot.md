# Discord Tracking Bot

A session may run a self-hosted Discord bot so the group can follow check,
DeathLink, and hint activity in a channel. The supported bot is
[bridgeipelago](https://github.com/Quasky/bridgeipelago) (v3.0.1 or newer),
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
- Keep the canonical clone beside the other repositories under
  `<workspace>/projects/repos/Awepeeps-bridgeipelago`, outside this repository.
  Do not clone into a Windows or WSL home directory. Keep the Linux virtual
  environment in `~/.local/share/bridgeipelago/venv`; it is runtime data, not
  another source checkout.
- A repo-local clone under the ignored `bridgeipelago/` path is recognized by
  [.worktreeinclude](../.worktreeinclude) so a worktree can run the bot without
  a re-clone. Only `bridgeipelago/config.json` is listed there; the clone's data
  folders and `.venv` are rebuildable and are deliberately not copied. If the
  clone must live in the repository, `bridgeipelago/` is the ignored path; do not
  use `.secrets/hidden/` for it, since that path is private generation workspace
  and is excluded from `.worktreeinclude`.
- The bot writes `logs/`, `RegistrationData/`, `ItemQueue/`, and `ArchData/`
  relative to its working directory, keyed by `UniqueID`. Run it from its own
  directory so those folders stay together.

## Host on WSL2

Native Windows is unsupported by bridgeipelago v3; use WSL2 (or Docker).

1. Install WSL2/Ubuntu if needed: `wsl --install -d Ubuntu` in an admin
   PowerShell, then reboot and set the Linux user.
2. Install prerequisites (skip any already present):
   `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip`
3. Clone our fork; `main` contains the reviewed Awepeeps patches:
   ```bash
   # Set this to the workspace root mounted in WSL.
   workspace=/mnt/d/dev/deathpie
   git clone https://github.com/Awepeeps/Awepeeps-bridgeipelago.git "$workspace/projects/repos/Awepeeps-bridgeipelago"
   cd "$workspace/projects/repos/Awepeeps-bridgeipelago"
   python3 -m venv ~/.local/share/bridgeipelago/venv
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install --upgrade pip
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install -r requirements.txt
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install "websockets<14"   # newer versions break the receive loop
   ```
4. Create `config.json` from the shipped template, apply the `LanguageFile`
   fix, and fill the values (see Configuration).
5. Run it interactively from the clone, or install it as a WSL service (below).
   The wrapper forces the `fork` start method, which the bot needs on Python
   3.14 (see Run as a WSL service):
   ```bash
   ~/.local/share/bridgeipelago/venv/bin/python -u -c "import multiprocessing as m, runpy; m.set_start_method('fork'); runpy.run_path('bridgeipelago.py', run_name='__main__')" config.json
   ```

The clone lives outside this repository, so `config.json` and the data folders
never enter Git. If a dependency will not build on the installed Python,
install Python 3.12 and recreate the venv with it.

Verified environment: WSL2 Ubuntu, Python 3.14.4, git 2.53, bridgeipelago
`awepeeps-patches` (based on `live-v3.0.1`, commit `91a24ff`), websockets
13.1, discord.py 2.7.1.

### Forks and local changes

- Upstream is
  [Quasky/bridgeipelago](https://github.com/Quasky/bridgeipelago). The org fork
  is
  [Awepeeps/Awepeeps-bridgeipelago](https://github.com/Awepeeps/Awepeeps-bridgeipelago),
  and the personal fork is
  [deathpie/Awepeeps-bridgeipelago](https://github.com/deathpie/Awepeeps-bridgeipelago),
  made from the org fork, so all three share one fork network.
- `main` contains the reviewed Awepeeps changes. Keep the long-lived
  `awepeeps-patches` branch for maintaining our deviations from the original
  release (`live-v3.0.1`, commit `91a24ff`). Merge reviewed updates into `main`
  and synchronize both owned forks; never publish changes to Quasky.
- The branch is pushed to both forks, so `Awepeeps/Awepeeps-bridgeipelago` and
  `deathpie/Awepeeps-bridgeipelago` stay identical. Push it to both after every
  change.
- To upgrade, merge the original release tag into `awepeeps-patches`, verify
  the result, and fast-forward `main` in both owned forks (see Upgrading).
- Current patches on `awepeeps-patches`:
  - The port-change announcement: `CheckArchHost()` already detects a new
    archipelago.gg room port, updates `config.json`, and reports it to the
    debug channel; our patch also announces the new address in the broadcast
    channel so players know where to reconnect.
  - The `$help` command, which posts the player-command list in the channel.
  - Optional connection announcements: `DiscordConfig.AnnounceConnection`
    defaults to `false`, suppressing the repeated debug-channel startup message.

The live clone's remotes follow this layout: `origin` for the personal fork,
`upstream` for the Awepeeps org fork, and `quasky` for the original
Quasky/bridgeipelago project. Fetch original release tags from `quasky` when
upgrading; publish our patches to `upstream` and `origin`.

### Upgrading

Maintain original-project upgrades on `awepeeps-patches`, then fast-forward
`main` after verification. Stop the service first so the bot does not run
against a tree that changes underneath it:

```bash
systemctl --user stop bridgeipelago
git fetch quasky --tags
git switch awepeeps-patches
git merge <new-upstream-tag>    # for example live-v3.0.2
~/.local/share/bridgeipelago/venv/bin/python -m pip install -r requirements.txt
~/.local/share/bridgeipelago/venv/bin/python -m unittest discover
git push upstream awepeeps-patches
git push origin awepeeps-patches
git switch main
git merge --ff-only awepeeps-patches
git push upstream main
git push origin main
systemctl --user start bridgeipelago
```

This preserves existing history and uses ordinary pushes to both owned forks.
Keep local `main` tracking `origin/main`; `quasky` is a read-only source.

`config.json` is unchanged from v3.0.0, so no migration is needed.

## Run as a WSL service

With systemd enabled in WSL, run the bot as a user service so it starts on boot
and restarts on failure.

Create `~/.config/systemd/user/bridgeipelago.service` (replace `<user>` with the
Linux username and `<workspace>` with `deathpie` or the owning workspace):

```ini
[Unit]
Description=Bridgeipelago Discord bot for Archipelago
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago
ExecStart=/home/<user>/.local/share/bridgeipelago/venv/bin/python -u -c "import multiprocessing as m, runpy; m.set_start_method('fork'); runpy.run_path('bridgeipelago.py', run_name='__main__')" config.json
Restart=on-failure
RestartSec=10
StandardOutput=append:/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out
StandardError=append:/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out

[Install]
WantedBy=default.target
```

The wrapper exists because Python 3.14 defaults the Linux multiprocessing start
method to `forkserver` (previously `fork`); bridgeipelago relies on the Discord
child process inheriting a global lock, so under `forkserver` the bot's command
loop dies with `NameError: name 'ToggleLock' is not defined`. Forcing `fork`
avoids it without patching the bot.

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now bridgeipelago
loginctl enable-linger "$USER"   # start on boot without an active login
systemctl --user status bridgeipelago
```

Logs go to `journalctl --user -u bridgeipelago -f` and the appended
`<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out`. Stop or restart with
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

Our session uses `ItemFilterConfig.BotItemFilterLevel` `2` (progression only
in the channel feed), saved in the ignored local `config.json` and provided
as the default in this repository's config template.
Other recommended defaults: `ItemFilterConfig.BotItemSpoilTraps` `false`,
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

**LanguageFile gotcha:** the v3.0.x `config.json.template` omits
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
5. Choose a bot channel; enable Developer Mode and copy its channel ID and
   your own user ID. A separate debug channel is optional.

For Awepeeps, set both `DiscordBroadcastChannel` and `DiscordDebugChannel` to
`1561407458973319288` (`#archipelago-notifications`) in the local `config.json`.
All channel-based bot commands, AP notifications, and admin/debug alerts use
that channel; `#archipelago` is reserved for human conversation. Keep credentials
in the ignored local config; the tracked config template leaves channel IDs blank.

To give an already-added bot a managed role, add the `bot` scope to the default
install settings and re-add the bot (kick it, then invite it again). Re-adding
does not change the token.

**Channel permissions:** the bot's managed role needs `View Channel` and
`Send Messages` in every configured channel, plus `Attach Files` for charts.
A staff-only channel
that denies `Send Messages` makes the bot's `on_ready` fail with
`403 Missing Access`, so use a bot-friendly debug channel (for example a
`#bot-commands`) or add a channel overwrite for the managed role.

## Daily status reports

The `awepeeps-patches` bot can automatically post the same outputs as
`/checkcount`, then `/checkgraph`, then `/deathcount` in the configured broadcast
channel. Add this
top-level section to the ignored local `config.json` to enable midnight reports:

```json
"DailyPostConfig": {
    "Enabled": true,
    "Time": "00:00",
    "Timezone": "America/New_York"
}
```

Restart the bot after changing these settings. `Time` uses 24-hour `HH:MM`;
`Timezone` is an IANA timezone and follows daylight saving changes. The template
defaults to disabled. Startup waits for the next scheduled time rather than
posting missed reports. If the running computer is suspended across the scheduled
time, it may deliver that report once on resume. Failed reports are logged and
the next scheduled attempt is the following day. The bot records the last
successful report date under the session's
ignored log directory to prevent duplicate daily posts after reconnects or restarts.
The death tally includes observed DeathLink events; the graph uses the existing
web tracker and remains unavailable with `SelfHostNoWeb` enabled.

## Registration and commands

Commands only work in the broadcast channel (`#archipelago-notifications` for
Awepeeps); the bot ignores messages everywhere else, including a separate debug
channel if one is configured. Commands are
case-sensitive and lowercase. `$register` links your Discord account to a slot; the other
player commands act on your registered slot(s). Upstream reference:
[bridgeipelago commands](https://github.com/Quasky/bridgeipelago#commands).

The `awepeeps-patches` bot also registers the player commands as native Discord
slash commands in the server containing the configured broadcast channel. Type
`/` and select Shamiko-Bot to browse them. The existing `$` commands continue to
work. Slash commands enforce the same broadcast channel restriction; confirmations
and `/help` are private, catch-up and registration lists arrive by DM, and charts
and requested hints are posted in the broadcast channel.

Use `/register slot:<exact slot name>`, `/groupcheck slot:<exact slot name>`,
and `/hint slot:<exact slot name> item:<item name>` for commands with arguments.
`/ketchmeup` has an optional filter with Everything (default), Useful and
progression, and Progression only choices. The other player command names match
the `$` versions below. Admin and configuration commands remain message-only.

The bot determines the server ID from the broadcast channel and syncs its player
command list once after connecting. It requires application-command authorization
and members need permission to use application commands in that channel. No new
bot token, public web endpoint, or room generation is needed.

Player commands (`$` syntax; slash equivalents are available in Discord):

| Command | Effect |
|---------|--------|
| `$help` | Post this list of player commands in the channel |
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

Admin commands (upstream calls these admin-only, but the bot does not check
who sent them, so anyone who can post in the broadcast channel can run them):

| Command | Effect |
|---------|--------|
| `$hello`, `$iloveyou` | Trivial responses |
| `$reloadtracker`, `$reloaddiscord` | Reload the tracker or the Discord client |
| `$setconfig <key> <value>` | Change a `config.json` value (`ArchipelagoPort`, URLs, `UniqueID`) |
| `$archinfo` | Debug details (only when `DebugMode` is on) |

## Notifications

The `awepeeps-patches` bot suppresses the "Bot connected. Debug control - Online."
message by default, including when `DiscordConfig.AnnounceConnection` is absent.
Discord can fire `on_ready` again after reconnecting, which previously posted
the same message each time. Set `AnnounceConnection` to `true` only to restore
that behavior; this is an on/off setting, not a daily limit. Restart the bot
after changing it. Other debug messages, errors, and room-port alerts keep
their existing behavior.

A WebSocket disconnect does not prove the room is asleep. Brief reconnects stay
quiet. After a going-away close followed by at least 60 seconds of refused
reconnects, the bot posts one connection-unavailable notice and a matching
restored notice after reconnection. The room link stays wrapped in angle
brackets so Discord does not fetch a preview that could wake the room.

There are two separate paths with separate filters:

- **Channel feed (not per-user, not opt-in).** Item events matching the configured
  filter are posted to the broadcast channel. The host sets the level in `config.json`
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
- **Room port changes.** When archipelago.gg restarts a paused room on a new
  port, the bot updates its own `config.json`, reports it in the debug channel,
  and (via the `awepeeps-patches` branch) posts the new address in the
  broadcast channel so players know where to reconnect.

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
- **The bot reconnects every ~12 s and never posts checks.** The log repeats
  `Unknown error in CheckDatapackage, returning False` and `DataPackage is
  invalid, requesting new one`, and `ErrorLog` shows
  `Error reading or validating datapackage: '<game>'`. v3.0.0 sends a bare
  `GetDataPackage`, which the current archipelago.gg server answers with an
  empty games dict, so `CheckDatapackage` fails and the bot loops. Upgrade to
  `live-v3.0.1`, which requests the room's game list explicitly.
- **`NameError: name 'ToggleLock' is not defined`.** Python 3.14 changed the
  Linux default multiprocessing start method to `forkserver`, so the Discord
  child process no longer inherits the global lock; the command loop dies the
  first time a port rescan is requested, which also breaks `$reloaddiscord`,
  `CycleDiscord`, and the port-change hand-off. Launch the bot with the `fork`
  wrapper (see Run as a WSL service), or build the venv with Python 3.12/3.13.

## Trust

bridgeipelago is a third-party application and has no license. Review the
release and source before running it, and never place its credentials in this
repository.
