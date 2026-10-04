# Cross-platform task runner for the repository scripts. `just --list` shows
# every recipe. Each recipe is a thin wrapper around a script under scripts/;
# the scripts remain the source of truth.
#
# Paths with spaces (for example the season "2026/3. Fall") are handled by the
# season/input/output variables, which the recipes quote. Override any variable
# on the command line, e.g.
#   just season="2026/4. Winter" input="2026/4. Winter/YAML" output="2026/4. Winter/.secrets/hidden" generate --dry-run
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

season := "2026/3. Fall"
archipelago := "C:\\ProgramData\\Archipelago"
input := season + "/YAML"
output := season + "/.secrets/hidden"

# List the recipes.
default:
    @just --list

# Validate structure, YAML, links, APWorld integrity, and ROM/secret safety.
validate:
    python scripts/validate_repo.py

# Byte-compile the repository scripts.
compile:
    python -m compileall -q scripts

# Validate and compile. Run this before asking for review.
check: validate compile

# Scaffold a new season or import inputs. Pass script arguments through.
scaffold *ARGS:
    python scripts/scaffold_session.py {{ARGS}}

# Compare a renamed or normalized player YAML. Pass the two file paths.
compare *ARGS:
    python scripts/compare_player_yaml.py {{ARGS}}

# Generate a session. Extra flags pass through, e.g. --dry-run or --run-id.
generate *ARGS:
    python scripts/generate_session.py --season "{{season}}" --archipelago "{{archipelago}}" --input "{{input}}" --output "{{output}}" {{ARGS}}

# Publish seed/spoiler artifacts for a run. Extra flags pass through, e.g. --dry-run.
publish run *ARGS:
    python scripts/publish_session_artifacts.py --season "{{season}}" --run "{{run}}" {{ARGS}}
