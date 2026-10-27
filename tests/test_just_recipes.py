"""Exercise real just argv forwarding without invoking lifecycle mutations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JUST = shutil.which('just')
STUB = '''import json, os, sys
from pathlib import Path
with open(os.environ['AWEPEEPS_RECIPE_CAPTURE'], 'a', encoding='utf-8') as stream:
    stream.write(json.dumps([Path(__file__).stem, sys.argv[1:]]) + '\\n')
raise SystemExit(int(os.environ.get('AWEPEEPS_RECIPE_EXIT', '0')))
'''


class JustRecipeTests(unittest.TestCase):
    def setUp(self):
        if JUST is None:
            self.fail('Install just >= 1.33 before running the repository checks.')
        self.temp = tempfile.TemporaryDirectory(prefix='just recipe paths with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copyfile(ROOT / 'justfile', self.root / 'justfile')
        (self.root / 'scripts').mkdir()
        for script in ('validate_repo', 'session_doctor', 'close_session', 'check_secrets',
                       'scaffold_session', 'compare_player_yaml', 'generate_session',
                       'host_session_room', 'publish_session_artifacts'):
            (self.root / 'scripts' / (script + '.py')).write_text(STUB, encoding='utf-8')
        for module in ('pip', 'compileall', 'unittest'):
            (self.root / (module + '.py')).write_text(STUB, encoding='utf-8')
        self.capture = self.root / 'captured argv.jsonl'
        self.env = {**os.environ, 'AWEPEEPS_RECIPE_CAPTURE': str(self.capture)}

    def run_recipe(self, *args, expected=0):
        self.capture.unlink(missing_ok=True)
        result = subprocess.run([JUST, *args], cwd=self.root, env=self.env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return [json.loads(line) for line in self.capture.read_text(encoding='utf-8').splitlines()]

    def test_every_wrapper_dispatches_to_its_tool(self):
        for recipe, args, tool in (
            ('setup', [], 'pip'), ('validate', [], 'validate_repo'),
            ('compile', [], 'compileall'), ('test', [], 'unittest'),
            ('smoke', [], 'unittest'), ('doctor', [], 'session_doctor'),
            ('config-check', ['config with spaces.json'], 'session_doctor'),
            ('close-session', ['run-id'], 'close_session'),
            ('secrets', ['--container'], 'check_secrets'),
            ('scaffold', ['--dry-run'], 'scaffold_session'),
            ('compare', ['before file.yaml', 'after file.yaml'], 'compare_player_yaml'),
            ('generate', ['--dry-run'], 'generate_session'),
            ('host', ['run-id', '--dry-run'], 'host_session_room'),
            ('publish', ['run-id', '--dry-run'], 'publish_session_artifacts'),
            ('publish-files', ['--dry-run'], 'publish_session_artifacts'),
        ):
            with self.subTest(recipe=recipe):
                calls = self.run_recipe(recipe, *args)
                self.assertEqual(calls[0][0], tool)

    def test_spaces_and_shell_characters_remain_single_literal_arguments(self):
        values = ['path with spaces', 'literal$money', 'a&b', 'semi;colon', 'a"quote', "single'quote"]
        self.assertEqual(self.run_recipe('doctor', *values), [['session_doctor', values]])
        season = '2099/1. Space & $literal'
        args = self.run_recipe('season=' + season, 'archipelago=install path & literal',
                               'generate', '--run-id', 'name with spaces', '--dry-run')[0][1]
        self.assertEqual(args, ['--season', season, '--archipelago', 'install path & literal',
                                '--input', season + '/YAML', '--output', season + '/.secrets/hidden',
                                '--run-id', 'name with spaces', '--dry-run'])

    def test_failed_child_status_propagates_and_stops_check(self):
        self.env['AWEPEEPS_RECIPE_EXIT'] = '17'
        calls = self.run_recipe('check', expected=17)
        self.assertEqual([call[0] for call in calls], ['validate_repo'])

    def test_check_runs_validate_compile_and_tests(self):
        self.assertEqual([call[0] for call in self.run_recipe('check')],
                         ['validate_repo', 'compileall', 'unittest'])

    def test_config_and_close_plan_preserve_flags(self):
        self.assertEqual(self.run_recipe('config-check', 'private config.json', '--expected-seed', 'trusted value'),
                         [['session_doctor', ['--config-only', '--bot-config', 'private config.json',
                                              '--expected-seed', 'trusted value']]])
        args = self.run_recipe('season=2099/1. CI', 'close-session', 'run-id')[0][1]
        self.assertEqual(args, ['--season', '2099/1. CI', '--run', 'run-id', '--dry-run'])

    def test_real_cli_help_routes_import_on_the_current_platform(self):
        for recipe, args in (('doctor', []), ('secrets', []), ('scaffold', []),
                             ('compare', []), ('generate', []), ('host', ['test-run']),
                             ('publish', ['test-run']), ('publish-files', []),
                             ('close-session', ['test-run'])):
            with self.subTest(recipe=recipe):
                result = subprocess.run([JUST, recipe, *args, '--help'], cwd=ROOT,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('usage:', result.stdout)


if __name__ == '__main__':
    unittest.main()
