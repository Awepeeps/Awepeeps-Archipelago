# Fall 2026 Games

> See main Archipelago resources: [Archipelago Resources](../../Archipelago.md)

## Session Links

- **Google Sheet**: [https://docs.google.com/spreadsheets/d/1IlNYQDSLKqZUsS2J3TWNT6ruRYM5FtXTUhhjQ3Qtxc4/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1IlNYQDSLKqZUsS2J3TWNT6ruRYM5FtXTUhhjQ3Qtxc4/edit?usp=sharing)
- **Archipelago Room**: [https://archipelago.gg/room/0wCKUEvVT5-gFpHWfy6mBw](https://archipelago.gg/room/0wCKUEvVT5-gFpHWfy6mBw)
- **YAML Configurations**: [YAML/](YAML/)
- **APWorld Files**: [APWorld/](APWorld/) ([Sekiro](APWorld/sekiro.apworld), [Pokemon Crystal](APWorld/pokemon_crystal.apworld), [Ori WotW](APWorld/ori_wotw.apworld), [Baldur's Gate 3 - ToT](APWorld/bg3tot.apworld))
- **Secrets and Spoilers**: [.secrets/](.secrets/)

## Run Dates

- **Start:** October 17, 2026 — 7:00 PM Eastern
- **Completed:** October 26, 2026 (Eastern)

## Final Status

As of October 26, 2026, all six players have reached their goals and all 2,068
locations have been checked or released. Mouseytoy completed Overcooked! 2 on October 26,
finishing the group's run.

| Player | Game | Locations | Goal |
|--------|------|-----------|------|
| deathpie | Sekiro: Shadows Die Twice | 748/748 | Complete |
| kriegsdorff | Pokemon Crystal | 530/530 | Complete |
| Jack Whitman | Super Mario 64 | 164/164 | Complete |
| propernoun | Ori and the Will of the Wisps | 378/378 | Complete |
| chickensalad | Baldur's Gate 3 - ToT | 213/213 | Complete |
| mouseytoy | Overcooked! 2 | 35/35 | Complete |

## Players & Games

| Player | Game |
|--------|------|
| deathpie | Sekiro: Shadows Die Twice |
| kriegsdorff | Pokemon Crystal |
| Jack Whitman | Super Mario 64 |
| propernoun | Ori and the Will of the Wisps |
| chickensalad | Baldur's Gate 3 - ToT |
| mouseytoy | Overcooked! 2 |

| Game | Info | Setup Guide | YAML | Release | Software | PopTracker | Misc. |
|------|------|-------------|------|---------|----------|------------|-------|
| Sekiro: Shadows Die Twice | [Info](https://github.com/yenix4/ArchipelagoSekiro/blob/main/worlds/sekiro/docs/en_Sekiro%20Shadows%20Die%20Twice.md) | [Setup Guide](https://github.com/yenix4/ArchipelagoSekiro/blob/main/worlds/sekiro/docs/setup_en.md) | [YAML](YAML/deathpie_Sekiro_v2.yaml) | [Release](https://github.com/yenix4/ArchipelagoSekiro/releases) | [Sekiro AP Client](https://github.com/antonovanton000/SekiroArchipelagoClient/releases) | [PopTracker](https://github.com/vonTungsten/Sekiro-Poptracker/releases) (early/incomplete) | Enemy randomizer uses [thefifthmatt's Sekiro randomizer](https://www.nexusmods.com/sekiro/mods/543); consider disabling for large multiworlds |
| Pokemon Crystal | [Info](https://github.com/gerbiljames/Archipelago-Crystal/blob/pokecrystal/worlds/pokemon_crystal/docs/en_Pokemon%20Crystal.md) | [Setup Guide](https://multiworld.gg/tutorial/Pokemon%20Crystal/setup_en) | [YAML](YAML/kriegsdorff_pokemon-crystal_v3.yaml) | [Release v6.0.2](https://github.com/gerbiljames/Archipelago-Crystal/releases/tag/6.0.2) | [BizHawk 2.9/2.10](https://tasvideos.org/BizHawk/ReleaseHistory) or [mGBA 0.10.3+](https://mgba.io/) | [PopTracker Pack](https://github.com/palex00/crystal-ap-tracker/releases/latest) | [Web client](https://gerbiljames.github.io/crystal-ap-web/) (generate YAMLs / play in-browser) |
| Super Mario 64 | [Info](https://archipelago.gg/games/Super%20Mario%2064/info/en) | [Setup Guide](https://archipelago.gg/tutorial/Super%20Mario%2064/setup_en) | [YAML](YAML/Jack%20Whitman_Super-Mario-64_v2.yaml) | - | [SM64AP-Launcher](https://github.com/N00byKing/SM64AP-Launcher/releases) | - | Archipelago `sm64ex` decomp/PC build required |
| Ori and the Will of the Wisps | [Info](https://github.com/Satisha10/APwotw_release) | [Setup Guide](https://github.com/Satisha10/APwotw_release#setup-guide) | [YAML](YAML/propernoun_Ori-and-the-Will-of-the-Wisps_v1.yaml) | [Release](https://github.com/Satisha10/APwotw_release/releases) | [WotW Randomizer](https://wotw.orirando.com/) | - | [Wiki](https://wiki.orirando.com/) |
| Baldur's Gate 3 - ToT | [Project](https://github.com/Zoltun456/Archipelago-BG3-ToT) | [Setup Guide](https://github.com/Zoltun456/Archipelago-BG3-ToT/blob/v1.2.2/README.md#install-guide) | [YAML](YAML/chickensalad_baldurs-gate-3-tot_v1.yaml) | [Release v1.2.2](https://github.com/Zoltun456/Archipelago-BG3-ToT/releases/tag/v1.2.2) | Windows PC, [BG3 Mod Manager](https://github.com/LaughingLeader/BG3ModManager) | - | Requires the matching `ArchipelagoToT.pak`, the `AdvancedTTSpells` mod, and the BG3 ToT Client |
| Overcooked! 2 | [Info](https://archipelago.gg/games/Overcooked%21%202/info/en) | [Setup Guide](https://archipelago.gg/tutorial/Overcooked%21%202/setup/en) | [YAML](YAML/mouseytoy_overcooked-2_v2.yaml) | - | [OC2-Modding client](https://github.com/toasterparty/oc2-modding/releases) | - | Windows 10+ PC required. Steam is recommended, and Epic is supported. GOG is not officially supported. Windows Store and consoles are unsupported. |

## Notes

- The supplied Crystal v3 YAML includes `allow_collecting_from`, which is absent from the v6.0.2 release template and ignored by Archipelago 0.6.7 with a warning. The supplied settings are preserved; generation succeeds, but that option has no effect in this run.
- Pokemon Crystal uses `pokemon_crystal.apworld` v6.0.2 from the linked release (requires Archipelago 0.6.7). Kriegsdorff's v3 evolution settings match its template: `Level and Stat` replaces the old `Level Tyrogue` name, and `Held Item` is supported in v6.0.2; v5.4.6 rejects these values. The release archive SHA-256 is `05dc593ee79bf76e4b6e4b10395359325d8cc7525b76fe1d19bbc3232a3d0a42`.
- Pokemon Crystal generation uses the local v1.1 ROM in the ignored `.roms/` directory. The host ROM path `../../../.roms/Pokemon - Crystal Version (UE) (V1.1) [C][!].gbc` resolves from the default `.secrets/hidden/<run-id>/` workspace; adjust it if using a different workspace root. The superseded v1.0 ROM has been removed locally, so only the V1.1 image remains in the stash.
- The October 10 test session uses the updated player v2 YAMLs and Pokemon Crystal APWorld v6.0.2. Its [seed](.secrets/revealed/2026-10-10_test/2026-10-10_seed.zip) and [spoiler](.secrets/revealed/2026-10-10_test/2026-10-10_spoiler.txt) are intentionally revealed before the official start date.
- The October 11 test session was generated from the current checked-in YAMLs with run ID `2026-10-11_test`. Kriegsdorff moved to `kriegsdorff_pokemon-crystal_v3.yaml`, changing two options from v2: `randomize_pokedex: vanilla` (was `randomize`) and `randomize_trainer_parties: match_types` (was `vanilla`). Its [seed](.secrets/revealed/2026-10-11_test/2026-10-11_seed.zip) and [spoiler](.secrets/revealed/2026-10-11_test/2026-10-11_spoiler.txt) are intentionally revealed.
- The official session was generated on October 17, 2026 from the current checked-in YAMLs with run ID `2026-10-17` and is hosted in the room linked above. Now that all six players have completed the session, its [seed](.secrets/revealed/2026-10-17/2026-10-17_seed.zip) and [spoiler](.secrets/revealed/2026-10-17/2026-10-17_spoiler.txt) are intentionally revealed. The rest of the generation workspace stays private under `.secrets/hidden/`.
- Generate this season from the repository inputs with `python scripts/generate_session.py --season "2026/3. Fall" --archipelago "C:\ProgramData\Archipelago" --dry-run`. Review all six playable players plus the `Bridgeipelago` spectator slot. Remove `--dry-run` only when the game setup and APWorld installation are ready. Output defaults to the ignored `2026/3. Fall/.secrets/hidden/<run-id>/` directory, with a date-only run ID when `--run-id` is omitted. Check both hidden and revealed run folders before relying on that default; use a unique explicit `--run-id` for a repeated or named run.
- The generator copies `YAML/.host.yaml` to the private workspace as `host.yaml` and runs Archipelago from that workspace, so omitted generator defaults come from the copied host file. An explicit option such as `--spoiler 1` overrides the host value for that run.
- After generation, run `python scripts/publish_session_artifacts.py --season "2026/3. Fall" --run <run-id> --dry-run`, review the destination, then rerun without `--dry-run` to copy `YYYY-MM-DD_seed.zip` and `YYYY-MM-DD_spoiler.txt` into the appropriate subfolder under `2026/3. Fall/.secrets/revealed/`. No extra `revealed` folder is created inside the private run; leave the full generation workspace private under `.secrets/hidden/`.
- The generator requires an installed Archipelago version at least as new as the highest `requires.version` in the playable YAMLs. It verifies the four season APWorld archives against `custom_worlds/`; add `--sync-apworlds` only to copy a reviewed archive when it is missing or differs.
- A fixed `--seed` selects a known numeric seed, but generated artifacts also depend on the Archipelago/APWorld/runtime state. Keep the private `generation-manifest.json` with any generated seed or spoiler so later runs can be compared against the exact checked-in inputs and generator executable.
- Super Mario 64 uses the Archipelago `sm64ex` decomp/PC build, not an emulator. Build it with [SM64AP-Launcher](https://github.com/N00byKing/SM64AP-Launcher/releases) or the manual process in the [setup guide](https://archipelago.gg/tutorial/Super%20Mario%2064/setup_en). The YAML controls the generated multiworld, while compile-time options are set when you build the executable.
- Jack's v2 YAML enables Move Randomizer and strict move requirements. The SM64 template marks the `nomoverando` branch as incompatible with Move Randomizer, so use a supported build.
- For online play, launch the built executable with `--sm64ap_name "Jack Whitman" --sm64ap_ip archipelago.gg:PORT`. A uniquely named build is normal for a custom configuration; an `.apsm64ex` patch file is for offline play and is not needed for the hosted-room flow.
- Super Mario 64's Archipelago integration is provided by the Archipelago `sm64ex` build, so no separate Fall APWorld file is needed for it.
- The Fall APWorld directory contains the Sekiro, Pokemon Crystal, Ori and the Will of the Wisps, and Baldur's Gate 3 - ToT world archives used by the corresponding YAMLs.
- Baldur's Gate 3 - ToT uses `bg3tot.apworld` v1.2.2. Install the matching `ArchipelagoToT.pak` from the linked v1.2.2 release and add the required `AdvancedTTSpells` mod. Follow the setup guide for the Mod Manager load order and client steps.
- The checked-in Super Mario 64 and Overcooked! 2 templates list Archipelago 0.6.7 as the minimum, but both imported YAMLs omit `requires.version`. Confirm the installed Archipelago version is at least 0.6.7 before generation.
- `Bridgeipelago` is the season's self-hosted Discord tracking bot. It joins as a spectator slot from `YAML/Bridgeipelago_Archipelago_v1.yaml` (game `Archipelago`; no items or locations, no effect on the multiworld). See [Discord tracking bot](../../docs/discord-bot.md) for hosting and configuration. Its `config.json` holds the Discord token and room password and must never be committed.
- ROMs are not provided or linked in this repository; see [Archipelago.md](../../Archipelago.md) for policy.
