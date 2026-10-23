# Admin guide

This guide covers commands for an existing Archipelago room. It does not create
or recreate rooms. For room creation, see the [session workflow](session-workflow.md).

## Where commands go

Use the **server command console** for room administration:

- For a hosted room, the room owner signs in to [archipelago.gg](https://archipelago.gg/)
  with the existing admin session and enters commands in that room's server console.
  The [hosting workflow](session-workflow.md#host-the-room) explains how the existing
  session is associated with the room. Never share or print the session identifier.
- For a self-hosted room, use that server process's console.
- Player commands beginning with `!` go in the player's Archipelago client chat.
  Discord slash commands and the tracking bot's `$` commands do not administer a room.

An offline player can still be targeted by a server-console command. Archipelago
operates on the slot in the currently hosted room and its existing seed/save state;
there is no need to edit a save file or seed file manually.

## Help a finished player: collect and release everything

For example, once chickensalad is finished, enter these separately in the
existing room's server console:

```text
/collect chickensalad
/release chickensalad
```

The first command delivers everything still owed to chickensalad. The second
releases items at their remaining locations to each item's intended recipient;
it does not let the admin redirect all those items to an arbitrary player.
Both work even if chickensalad is offline. The server records the deliveries,
and their client receives outstanding items when they reconnect.

## Release and collect for named players

Enter a player slot name after the command. Quote names containing spaces.

```text
/release "Player Name"
/collect "Player Name"
```

`/release` sends that player's remaining items at unchecked locations to their
recipients. `/collect` sends that player's remaining items from across the
multiworld to them. These admin commands can target an offline slot and bypass
the player's goal restriction. They are distinct actions; use the one that fits
the situation and verify the intended slot first.

## Grant an item

`/send` gives an item to a named player. It creates an item grant; it does not
release the player's remaining locations.

```text
/send "Player Name" Item Name
```

The player name is one argument (quote it when it contains spaces); the item
name is the remainder of the command. Check the server response and target
carefully before using this command.

## Give a free hint

```text
/hint "Player Name" Item Name
```

The server's admin hint command creates a hint for that player without spending
their hint points. Use the exact item name from that player's game. The official command list and
the [Archipelago 0.6.7 server implementation](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.7/MultiServer.py)
are references. In that version, the host `/hint` handler resolves items and
item groups, not location names, and `/hint_location` is not an admin server
command. Player `!hint_location` is a separate client-chat command.

## Hint cost: live room and future defaults

The current community default recorded in the player guide is 25%. The examples
below explain how to change it to 10% when the host is ready; this documentation
change does not alter any running room or YAML.

For a live room, an authorized room operator may change the percentage with the
server console command:

```text
/option hint_cost 10
/save
```

The option changes the current room's hint cost; connected clients receive the
updated room option.
`/save` writes the running server state after the option change. The setting is
restored with that server save; it does not rewrite the seed's embedded options
or a season YAML. Confirm the server's success response and ask a player to use
`!hint` to verify the displayed cost. If inspecting `/options`, keep its output
private because it may include the room password.

At one point per checked location, a 200-check world provides 200 points: at
25%, a hint costs 50 points; at 10%, it costs 20.

For a future season's default, maintainers can set `server_options.hint_cost: 10`
in that season's `YAML/.host.yaml` when making the corresponding configuration
change. Do not edit an archived season's settings as part of that future change.
A host config edit affects generation defaults; it does not update an already
running room or retroactively change options embedded in an existing seed.

## References

- [Official Archipelago command guide](https://archipelago.gg/tutorial/Archipelago/commands_en)
- [Archipelago 0.6.7 MultiServer.py](https://github.com/ArchipelagoMW/Archipelago/blob/0.6.7/MultiServer.py)
- [Player guide](player-guide.md)
