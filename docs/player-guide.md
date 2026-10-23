# Player guide

These are our current community defaults. A season's own
`YAML/.host.yaml` is the reference for that season; a host can override settings
in the running room.

- **Hints:** `hint_cost: 25`, with `location_check_points: 1`: each check earns
  one hint point, and a hint costs points equal to 25% of your world's checks
  (for example, 50 points in a 200-check world).
- **Release and collect:** both modes are `goal`. Players may use them once
  the server has registered their own goal completion. They are manual, not
  automatic, and you do not need to wait for everyone else to finish.
- **Remaining items:** `remaining_mode: goal` allows `!remaining` after your
  goal. Item cheats via `!getitem` are disabled.
- **Discord:** item notifications are progression-only in
  `#archipelago-notifications`. The midnight Eastern report posts check counts,
  the progress graph, then the DeathLink tally. See [Discord bot settings](discord-bot.md).

## Players: hints during your run

While connected to your own player slot, send these in your game's
**Archipelago client chat** (or the Archipelago Text Client):

- `!hint` lists your existing hints, available hint points, and the current
  cost. Use this first to check your balance.
- `!hint <item name>` requests a hint showing which world and location hold
  an item for you. Replace `<item name>` with the actual item name.
- `!hint_location <location name>` requests a hint about the item at a
  particular location in your world.

New hints spend points earned by checking locations; our default cost is
described above. You can use hints while playing, before completing your goal.

In Discord's `#archipelago-notifications`, Shamiko-Bot also offers:

- `/register slot:<your exact slot name>` to link your player slot first.
- `/hints` to DM existing hints for your registered slots.
- `/hint slot:<slot name> item:<item name>` to request an item hint through
  the bot. The bot posts a public note naming you and the request (without
  pinging anyone), and posts the result in the channel when the server reveals
  it, if the host relays hint results.

The Discord commands and client chat commands use different syntax. See
[Discord command details](discord-bot.md#registration-and-commands) for setup
and the full list.

## Players: release and collect after your goal

Stay connected to your own slot and send these commands in your game's
**Archipelago client chat**. If your client cannot send chat, use the Archipelago
Text Client to connect to the same room as your player slot. These are not
Discord slash commands.

1. Confirm that the server has registered your goal completion. Finishing the
   game locally is not enough if the client has not reported it; if a command
   says you have not finished, check your client connection and goal status.
2. Send `!release` to send out the items still at unchecked locations in your
   world to their owners. This helps players who are still playing.
3. Optionally send `!collect` to receive your own remaining items from locations
   across the multiworld, even if those locations have not been checked yet.

For example, after chickensalad's goal is registered, chickensalad can send
`!release` and then `!collect` from their own connected client. The player
commands take no player-name argument. Release and collect are separate actions;
doing one does not automatically do the other.

Room administrators: see the [Admin guide](admin-guide.md) for server-console
commands, including release and collect for named players.

For the full player command reference, see the
[official Archipelago command guide](https://archipelago.gg/tutorial/Archipelago/commands_en).
