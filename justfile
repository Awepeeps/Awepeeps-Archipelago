# Canonical task entry point. Requires just >= 1.33 and Python >= 3.12 on PATH.
# Script recipes forward argv directly; user paths are never interpolated into code.
set positional-arguments

season := "2026/3. Fall"
archipelago := if os_family() == "windows" { "C:/ProgramData/Archipelago" } else { "" }
input := season + "/YAML"
output := season + "/.secrets/hidden"
export AWEPEEPS_TASK_SEASON := season
export AWEPEEPS_TASK_ARCHIPELAGO := archipelago
export AWEPEEPS_TASK_INPUT := input
export AWEPEEPS_TASK_OUTPUT := output

# List available recipes.
[script('python')]
@default:
    import subprocess
    raise SystemExit(subprocess.call(["just", "--list"]))

# Install validation/test dependencies.
[script('python')]
@setup:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-dev.txt"]))

# Validate tracked files and public archives.
[script('python')]
@validate:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/validate_repo.py"]))

# Compile the repository scripts.
[script('python')]
@compile:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "-m", "compileall", "-q", "scripts"]))

# Run the offline script and recipe tests.
[script('python')]
@test *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", *sys.argv[1:]]))

# Exercise the real just wrappers using isolated synthetic tools.
[script('python')]
@smoke:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_just_recipes.py", "-v"]))

# Read-only checkout/config diagnostics.
[script('python')]
@doctor *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/session_doctor.py", *sys.argv[1:]]))

# Check a private config without displaying values.
[script('python')]
@config-check config *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/session_doctor.py", "--config-only", "--bot-config", *sys.argv[1:]]))

# Plan closure only; never stop services or mutate a room.
[script('python')]
@close-session run *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/close_session.py", "--season", os.environ["AWEPEEPS_TASK_SEASON"], "--run", sys.argv[1], "--dry-run", *sys.argv[2:]]))

# Redacted full-history Gitleaks scan (native CLI or --container).
[script('python')]
@secrets *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/check_secrets.py", *sys.argv[1:]]))

# Scaffold/import a season; start with --dry-run.
[script('python')]
@scaffold *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/scaffold_session.py", *sys.argv[1:]]))

# Compare player YAML settings.
[script('python')]
@compare *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/compare_player_yaml.py", *sys.argv[1:]]))

# Generate a session; start with --dry-run.
[script('python')]
@generate *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/generate_session.py", "--season", os.environ["AWEPEEPS_TASK_SEASON"], "--archipelago", os.environ["AWEPEEPS_TASK_ARCHIPELAGO"], "--input", os.environ["AWEPEEPS_TASK_INPUT"], "--output", os.environ["AWEPEEPS_TASK_OUTPUT"], *sys.argv[1:]]))

# Host a generated run; start with --dry-run.
[script('python')]
@host run *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/host_session_room.py", "--season", os.environ["AWEPEEPS_TASK_SEASON"], "--run", sys.argv[1], *sys.argv[2:]]))

# Publish a saved run; start with --dry-run.
[script('python')]
@publish run *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/publish_session_artifacts.py", "--season", os.environ["AWEPEEPS_TASK_SEASON"], "--run", sys.argv[1], *sys.argv[2:]]))

# Publish explicit staged artifacts; start with --dry-run.
[script('python')]
@publish-files *args:
    import os, subprocess, sys
    raise SystemExit(subprocess.call([sys.executable, "scripts/publish_session_artifacts.py", "--season", os.environ["AWEPEEPS_TASK_SEASON"], *sys.argv[1:]]))

# Validate, compile, and run all offline tests through the same entry point as CI.
check: validate compile test
