"""Synthetic publication fixtures: never read private session inputs."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import pickle
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import seed_safety as safety
import publish_session_artifacts as publish
import validate_repo as validator


def encoded(data):
    return b'\x03' + zlib.compress(pickle.dumps(data, protocol=4))


class PublicationSafetyTests(unittest.TestCase):
    def test_large_integer_keys_cannot_amplify_repeated_hash_work(self):
        for key in (1 << 129, (1 << 129,), frozenset([1 << 129])):
            with self.subTest(key_type=type(key).__name__), self.assertRaisesRegex(
                    safety.SeedSafetyError, 'integer key size limit'):
                safety.validate_multidata(encoded({'server_options': {}, key: None}))
        safety.validate_multidata(encoded({'server_options': {}, (1 << 127): None}))

    def test_integer_hash_collision_flood_is_rejected(self):
        import sys
        from pickle import FROZENSET, MARK, NONE, SETITEMS, STOP
        # Keys spaced by Python's modulus have identical hashes. Construct the
        # wire form directly so building the fixture itself does no hashing.
        keys = [pickle.dumps(i * sys.hash_info.modulus, protocol=4)[2:-1]
                for i in range(64)]
        header = b'\x80\x04}\x8c\x0eserver_options}s'
        dict_body = MARK + b''.join(key + NONE for key in keys) + SETITEMS
        frozen_body = b'\x8c\x05items' + MARK + b''.join(keys) + FROZENSET + b's'
        for body in (dict_body, frozen_body):
            with self.subTest(body=body[:8]), self.assertRaisesRegex(
                    safety.SeedSafetyError, 'hash collision limit'):
                safety.validate_multidata(b'\x03' + zlib.compress(header + body + STOP))

    def test_memoized_tuple_hash_bomb_is_rejected_before_native_hashing(self):
        # A ~300-byte key otherwise takes exponentially many Python hash steps.
        header = b'\x80\x04}\x8c\x0eserver_options}s'
        dag = b'K\x00\x85q\x00'
        for depth in range(1, 51):
            dag += b'h' + bytes([depth - 1]) + b'\x86q' + bytes([depth])
        cases = (
            header + dag + b'Ns.',                       # SETITEM
            header + b'(' + dag + b'Nu.',                # SETITEMS
            header + b'\x8c\x05items\x8f(' + dag + b'\x90s.',  # ADDITEMS
            header + b'\x8c\x05items(' + dag + b'\x91s.',       # FROZENSET
        )
        for raw in cases:
            with self.subTest(raw=raw[-8:]), self.assertRaisesRegex(
                    safety.SeedSafetyError, 'hash complexity|oversized multidata key'):
                safety.validate_multidata(b'\x03' + zlib.compress(raw))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, data=None, extra=None):
        path = self.root/'seed.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('AP_test.archipelago', encoded(data or {'server_options': {'password': None}}))
            for name, content in (extra or {}).items(): archive.writestr(name, content)
        return path

    def test_valid_current_seed(self):
        publish.validate_seed(self.archive({'server_options': {'password': '', 'server_password': None},
            'version': (0, 6, 3), 'locations': {1: {100: (200, 1, 0)}},
            'spheres': [{1: {100, 101}}], 'slot_data': {1: {'enabled': True}}}))

    def test_passwords_rejected_without_disclosing_value(self):
        for field in ('password', 'server_password'):
            for data in ({'server_options': {field: 'do-not-print-this'}},
                         {'server_options': {}, 'slot_data': {1: {field: 'do-not-print-this'}}}):
                with self.subTest(field=field), self.assertRaises(publish.PublishError) as caught:
                    publish.validate_seed(self.archive(data))
                self.assertIn(field, str(caught.exception))
                self.assertNotIn('do-not-print-this', str(caught.exception))

    def test_malicious_pickle_cannot_execute(self):
        sentinel = self.root/'executed'
        class Payload:
            def __reduce__(self):
                return eval, (f"__import__('pathlib').Path({str(sentinel)!r}).write_text('bad')",)
        with self.assertRaises(safety.SeedSafetyError):
            safety.validate_multidata(encoded({'server_options': {}, 'payload': Payload()}))
        self.assertFalse(sentinel.exists())
        for raw in (b'cposix\nsystem\n.', b'Psecret\n.', b'\x80\x04}b.',
                    b'cworlds.example.Options\nCustomOption\n.'):
            with self.assertRaises(safety.SeedSafetyError):
                safety.validate_multidata(b'\x03'+zlib.compress(raw))

    def test_inert_ap_netutils_records_and_enums(self):
        raw = (b'\x80\x04}\x8c\x0eserver_options}s\x8c\x04slot'
               b'cNetUtils\nNetworkSlot\n(\x8c\x04name\x8c\x04game'
               b'cNetUtils\nSlotType\nK\x01\x85R)t\x81s.')
        safety.validate_multidata(b'\x03'+zlib.compress(raw))

    def test_malformed_and_oversized(self):
        for data in (b'', b'\x04abc', b'\x03invalid', b'\x03'+zlib.compress(b'bad'),
                     encoded({'server_options': {}})+b'trailer',
                     b'\x03'+zlib.compress(pickle.dumps({'server_options': {}})+b'trailer'),
                     encoded({'not_server_options': {}})):
            with self.subTest(data=data[:4]), self.assertRaises(safety.SeedSafetyError):
                safety.validate_multidata(data)
        with patch.object(safety, 'MAX_MULTIDATA', 64), self.assertRaises(safety.SeedSafetyError):
            safety.validate_multidata(encoded({'server_options': {}, 'padding': 'x'*10000}))
        with patch.object(safety, 'MAX_OPS', 2), self.assertRaises(safety.SeedSafetyError):
            safety.validate_multidata(encoded({'server_options': {}}))
        with patch.object(safety, 'MAX_MEMBER', 1), self.assertRaises(publish.PublishError):
            publish.validate_seed(self.archive())
        with patch.object(safety, 'MAX_ARCHIVE', 1), self.assertRaises(publish.PublishError):
            publish.validate_seed(self.archive())

    def test_private_and_rom_archive_entries(self):
        for name in ('.admin/session_id.env', '.env.production', 'config.json',
                     '.secrets/hidden/spoiler.txt', 'room.json', 'host.yaml',
                     'AP_seed.apsave', '../escaped.txt', 'game.sfc', 'nested\\.env'):
            with self.subTest(name=name), self.assertRaises(publish.PublishError):
                publish.validate_seed(self.archive(extra={name: 'do-not-print-this'}))

    def test_missing_duplicate_corrupt_archive(self):
        path = self.root/'seed.zip'
        with zipfile.ZipFile(path, 'w') as archive: archive.writestr('patch.aptest', b'patch')
        with self.assertRaises(publish.PublishError): publish.validate_seed(path)
        with self.assertRaises(publish.PublishError):
            publish.validate_seed(self.archive(extra={'other.archipelago': encoded({'server_options': {}})}))
        path.write_bytes(b'not a zip')
        with self.assertRaises(publish.PublishError): publish.validate_seed(path)

    def test_tracked_credentials_and_allowed_templates(self):
        with patch.object(validator, 'ROOT', self.root):
            for name in ('.admin/session_id.env', '.ENV', '.env.local', 'nested/private.env',
                         'bridgeipelago/config.json', 'actualbot/config.json', 'nested/.admin/token',
                         '.envrc', 'credentials.json', '.ssh/id_rsa'):
                errors = []; validator.validate_tracked_safety([self.root/name], errors)
                self.assertTrue(errors, name)
            for name in ('.worktreeinclude', '.env.example', '.env.production.template',
                         'docs/bridgeipelago.config.template.json', 'docs/config.json.template'):
                errors = []; validator.validate_tracked_safety([self.root/name], errors)
                self.assertEqual(errors, [], name)

    def test_validator_uses_same_gate(self):
        folder = self.root/'.secrets/revealed'; folder.mkdir(parents=True)
        path = folder/'seed.zip'
        path.write_bytes(self.archive({'server_options': {'password': 'do-not-print-this'}}).read_bytes())
        with patch.object(validator, 'ROOT', self.root):
            errors = []; validator.validate_revealed_archives([path], errors)
        self.assertEqual(len(errors), 1)
        self.assertIn('password', errors[0]); self.assertNotIn('do-not-print-this', errors[0])

    def manifest(self):
        season = self.root/'season'; run = self.root/'run'
        (season/'YAML').mkdir(parents=True); (run/'Players').mkdir(parents=True)
        (season/'YAML/.host.yaml').write_text('original host')
        (run/'host.yaml').write_text('original host')
        (run/'Players/player_game_v1.yaml').write_text('name: player')
        def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
        (run/'generation-manifest.json').write_text(json.dumps({
            'host_sha256': digest(run/'host.yaml'), 'apworlds': [],
            'players': [{'file': 'player_game_v1.yaml', 'sha256': digest(run/'Players/player_game_v1.yaml')}]}))
        return season, run

    def test_current_host_drift_is_informational(self):
        season, run = self.manifest()
        (season/'YAML/.host.yaml').write_text('changed current host')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            publish.validate_generation_manifest(run, season)
        self.assertIn('Info:', out.getvalue())

    def test_saved_host_tampering_rejected(self):
        season, run = self.manifest()
        (run/'host.yaml').write_text('tampered snapshot')
        with self.assertRaisesRegex(publish.PublishError, 'saved snapshot'):
            publish.validate_generation_manifest(run, season)


if __name__ == '__main__': unittest.main()
