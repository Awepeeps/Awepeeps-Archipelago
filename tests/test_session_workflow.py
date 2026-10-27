"""Offline, temporary-directory tests for read-only workflow helpers."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_secrets
import close_session
import session_doctor


def valid_config():
    return {
        "DiscordConfig": {
            "DiscordToken": "private-test-token",
            "DiscordBroadcastChannel": "123456789",
            "DiscordDebugChannel": "987654321",
        },
        "ArchipelagoConfig": {
            "ArchipelagoBotSlot": "private-slot",
            "UniqueID": "private-id",
            "ExpectedSeedName": "private-seed",
            "ArchipelagoPassword": "private-password",
            "ArchipelagoPort": 12345,
            "ArchipelagoServerURL": "https://archipelago.gg/room/private-room",
            "ArchipelagoTrackerURL": "https://archipelago.gg/tracker/private-tracker",
        },
        "DailyPostConfig": {"Enabled": False, "DeathLinkSlots": ["private-slot"]},
        "MetaConfig": {"LanguageFile": "en"},
    }


class SessionWorkflowTests(unittest.TestCase):
    def test_container_secret_scan_is_pinned_read_only_and_redacted(self):
        with patch('check_secrets.shutil.which', return_value='docker'), patch(
                'check_secrets.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(check_secrets.main(['--container', '--repo', '.']), 0)
        command = run.call_args.args[0]
        self.assertIn('--redact=100', command)
        self.assertIn('--log-opts=--all', command)
        self.assertIn('none', command)
        self.assertTrue(any(arg.endswith(':/repo:ro') for arg in command))
        self.assertTrue(any('@sha256:' in arg for arg in command))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session workflow ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "private config.json"

    def write_config(self, data):
        self.config.write_text(json.dumps(data), encoding="utf-8")

    def assert_no_private_values(self, output):
        for value in ("private-test-token", "123456789", "987654321", "private-id", "private-password", "private-slot", "private-seed", "private-room", "private-tracker"):
            self.assertNotIn(value, output)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_config_cli_path_with_spaces_read_only_and_redacted(self):
        self.write_config(valid_config())
        before = self.snapshot()
        with patch("session_doctor.subprocess.run", side_effect=AssertionError("must not run processes in config-only mode")):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = session_doctor.main(["--repo", str(self.root), "--config-only", "--bot-config", self.config.name, "--expected-seed", "private-seed"])
        self.assertEqual(code, 0)
        self.assert_no_private_values(output.getvalue())
        self.assertEqual(before, self.snapshot())

    def test_invalid_config_values_never_echoed(self):
        config = valid_config()
        config["DiscordConfig"]["DiscordBroadcastChannel"] = "private-password"
        config["ArchipelagoConfig"]["ArchipelagoPort"] = "private-password"
        config["ArchipelagoConfig"]["ArchipelagoServerURL"] = "https://private-test-token:private-password@example.org/room/private-room"
        config["DailyPostConfig"]["DeathLinkSlots"] = {"private-password": "private-id"}
        self.write_config(config)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = session_doctor.main(["--config-only", "--bot-config", str(self.config), "--expected-seed", "other-private-seed"])
        self.assertEqual(code, 1)
        self.assert_no_private_values(output.getvalue())
        self.assertIn("DeathLinkSlots", output.getvalue())

    def test_malformed_or_missing_config_has_safe_error(self):
        for text in ('{"private-test-token":private-password}', "[]", "null"):
            with self.subTest(text=text):
                self.config.write_text(text, encoding="utf-8")
                errors, _ = session_doctor.validate_config(self.config)
                self.assertTrue(errors)
                self.assert_no_private_values(str(errors))
        self.assertTrue(session_doctor.validate_config(self.root / "missing")[0])

    def test_invalid_seed_type_and_deathlink_types_fail_safely(self):
        for value in (True, 12345, {}, ["private-password"]):
            with self.subTest(value=value):
                config = valid_config()
                config["ArchipelagoConfig"]["ExpectedSeedName"] = value
                self.write_config(config)
                errors, _ = session_doctor.validate_config(self.config, "private-seed")
                self.assertTrue(errors)
                self.assert_no_private_values(str(errors))
        for slots, has_error in ((None, False), ([], False), (["private-slot"], False), ("private-slot", True), ([""], True), (["a", "a"], True)):
            config = valid_config()
            config["DailyPostConfig"]["DeathLinkSlots"] = slots
            self.write_config(config)
            self.assertEqual(bool(session_doctor.validate_config(self.config)[0]), has_error)

    def test_git_failure_stderr_redacted_and_nonzero(self):
        for failure in (FileNotFoundError("private-test-token"), subprocess.CalledProcessError(1, "git", stderr="private-password"), subprocess.TimeoutExpired("git", 15)):
            with self.subTest(failure=type(failure).__name__), patch("session_doctor.subprocess.run", side_effect=failure):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = session_doctor.main(["--repo", str(self.root)])
                self.assertEqual(code, 1)
                self.assert_no_private_values(output.getvalue())

    def test_real_git_inspection_is_read_only_and_does_not_echo_remote_credentials(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin", "https://private-test-token:private-password@example.invalid/private-id"], check=True, capture_output=True)
        before = self.snapshot()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = session_doctor.main(["--repo", str(self.root)])
        self.assertEqual(code, 0)
        self.assert_no_private_values(output.getvalue())
        self.assertEqual(before, self.snapshot())

    def test_close_plan_is_read_only_and_requires_dry_run(self):
        season = self.root / "2026" / "3. Fall"
        season.mkdir(parents=True)
        (season / "README.md").write_text("# Session\n", encoding="utf-8")
        before = self.snapshot()
        output = io.StringIO()
        with patch("subprocess.run", side_effect=AssertionError("planner must not execute commands")), contextlib.redirect_stdout(output):
            code = close_session.main(["--repo", str(self.root), "--season", "2026/3. Fall", "--run", "2026-10-01", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("stop AND disable", output.getvalue())
        self.assertIn("MISSING", output.getvalue())
        self.assertEqual(before, self.snapshot())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            close_session.main(["--repo", str(self.root), "--season", "2026/3. Fall", "--run", "2026-10-01"])

    def test_close_rejects_escaping_paths(self):
        (self.root / "README.md").write_text("root", encoding="utf-8")
        for season, run in (("..", "run"), (".", "run"), ("2026/3. Fall", "../run")):
            with self.subTest(season=season, run=run), self.assertRaises(ValueError):
                close_session.closure_plan(self.root, season, run)

    def test_secret_scanner_missing_or_failed_is_not_success(self):
        with patch("check_secrets.shutil.which", return_value=None), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_secrets.main([]), 1)
        with patch("check_secrets.shutil.which", return_value="gitleaks"), patch("check_secrets.subprocess.run", return_value=subprocess.CompletedProcess([], 7)) as run:
            self.assertEqual(check_secrets.main(["--repo", str(self.root)]), 7)
            self.assertIn("--redact=100", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
