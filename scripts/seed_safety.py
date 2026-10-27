"""Fail-closed, data-only checks for public Archipelago seed archives.

AP 0.6.x Main.py writes format byte 3 + zlib(restricted_dumps(multidata)):
https://github.com/ArchipelagoMW/Archipelago/blob/0.6.3/Main.py#L290-L317
This interpreter supports primitive pickle data and inert NetUtils records/enums.
It never imports globals, calls pickle constructors, or imports APWorld code.
Other formats/opcodes/globals require an explicit reviewed parser update.
"""
from __future__ import annotations

import pickletools
import zlib
import zipfile
from pathlib import Path, PurePosixPath

MAX_MULTIDATA = 16 * 1024 * 1024
MAX_MEMBER = 128 * 1024 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_OPS = 2_000_000
MAX_ENTRIES = 4096


class SeedSafetyError(ValueError):
    """Public diagnostics include paths/field names only, never payload values."""


def private_location(name: str, *, archive: bool = False) -> bool:
    parts = PurePosixPath(name.replace('\\', '/').lower()).parts
    base = parts[-1] if parts else ''
    if any(p in {'.admin', '.roms', '.generated-secrets-hidden', '.ssh', '.aws', '.azure'} for p in parts):
        return True
    if '.secrets' in parts and 'hidden' in parts:
        return True
    template = base.endswith(('.example', '.sample', '.template'))
    if (base.startswith('.env') or base.endswith('.env')) and not template:
        return True
    if base in {'config.json', 'credentials.json', 'credentials.yaml', 'credentials.yml',
                'id_rsa', 'id_ed25519'}:
        return True
    return archive and (base in {'room.json', 'host.yaml', '.host.yaml', 'session_id',
                                'generation-manifest.json'} or
                        base.endswith(('.apsave', '.apsave.bak', '.pem', '.key')) or
                        any(p in {'registrationdata', 'itemqueue', 'archdata', 'logs'} for p in parts))


class _Global:
    def __init__(self, name: str):
        self.name = name


RECORDS = {'NetworkSlot', 'NetworkItem', 'Hint'}
ENUMS = {'SlotType', 'HintStatus', 'ClientStatus'}


def _check_hash_cost(value: object) -> None:
    """Bound expanded tuple hashing before Python hashes a key or set member.

    Memoized pickle tuples can form a tiny DAG with exponential hash cost.
    Counting expanded nodes (without deduplication) rejects that case before
    native dict/set operations, while permitting ordinary AP tuple keys.
    """
    pending = [(value, 0)]
    remaining = 128
    while pending:
        item, depth = pending.pop()
        remaining -= 1
        if remaining < 0 or depth > 8:
            raise SeedSafetyError('multidata hash complexity limit exceeded')
        if type(item) is int and item.bit_length() > 128:
            # Unlike strings/bytes, Python integers do not cache their hashes.
            # Reusing a memoized enormous integer across containers must not
            # repeatedly hash megabytes of digits for one cheap opcode.
            raise SeedSafetyError('multidata integer key size limit exceeded')
        if type(item) in {type(None), bool, int, float, str, bytes}:
            continue
        if type(item) not in {tuple, frozenset} or len(item) > remaining:
            raise SeedSafetyError('unsupported or oversized multidata key')
        pending.extend((child, depth + 1) for child in item)


def _data_pickle(raw: bytes) -> object:
    """Interpret a bounded primitive subset; even REDUCE/NEWOBJ are data-only."""
    stack: list = []
    memo: dict = {}
    hash_counts: dict = {}
    mark = object()

    def check_key(target: object, key: object) -> None:
        _check_hash_cost(key)
        # Integer keys have deterministic hashes: byte/opcode bounds alone do
        # not stop a small collision flood from causing quadratic insertion.
        # Retain the target so an object id cannot be reused during parsing.
        counts = hash_counts.setdefault(id(target), (target, {}))[1]
        fingerprint = hash(key)
        count = counts.get(fingerprint, 0) + 1
        if count > 32:
            raise SeedSafetyError('multidata hash collision limit exceeded')
        counts[fingerprint] = count

    def pop_mark() -> list:
        index = len(stack) - 1
        while index >= 0 and stack[index] is not mark:
            index -= 1
        if index < 0:
            raise SeedSafetyError('malformed multidata pickle')
        items = stack[index + 1:]
        del stack[index:]
        return items

    def global_value(module: str, name: str) -> _Global:
        if module != 'NetUtils' or name not in RECORDS | ENUMS:
            raise SeedSafetyError('unsupported multidata pickle global')
        return _Global(name)

    try:
        for count, (op, arg, pos) in enumerate(pickletools.genops(raw), 1):
            if count > MAX_OPS:
                raise SeedSafetyError('multidata opcode limit exceeded')
            code = op.name
            if code in {'PROTO', 'FRAME'}:
                continue
            if code == 'MARK': stack.append(mark)
            elif code == 'NONE': stack.append(None)
            elif code in {'NEWTRUE', 'NEWFALSE'}: stack.append(code == 'NEWTRUE')
            elif code in {'BININT', 'BININT1', 'BININT2', 'LONG1', 'LONG4', 'BINFLOAT',
                          'SHORT_BINUNICODE', 'BINUNICODE', 'BINUNICODE8', 'SHORT_BINBYTES',
                          'BINBYTES', 'BINBYTES8'}: stack.append(arg)
            elif code == 'EMPTY_DICT': stack.append({})
            elif code == 'EMPTY_LIST': stack.append([])
            elif code == 'EMPTY_SET': stack.append(set())
            elif code == 'EMPTY_TUPLE': stack.append(())
            elif code == 'MEMOIZE': memo[len(memo)] = stack[-1]
            elif code in {'BINPUT', 'LONG_BINPUT'}:
                if arg > MAX_OPS: raise SeedSafetyError('multidata memo limit exceeded')
                memo[arg] = stack[-1]
            elif code in {'BINGET', 'LONG_BINGET'}: stack.append(memo[arg])
            elif code == 'TUPLE': stack.append(tuple(pop_mark()))
            elif code in {'TUPLE1', 'TUPLE2', 'TUPLE3'}:
                n = int(code[-1]); values = stack[-n:]; del stack[-n:]; stack.append(tuple(values))
            elif code in {'APPENDS', 'ADDITEMS', 'SETITEMS'}:
                values = pop_mark(); target = stack[-1]
                if code == 'APPENDS' and type(target) is list: target.extend(values)
                elif code == 'ADDITEMS' and type(target) is set:
                    for value in values: check_key(target, value)
                    target.update(values)
                elif code == 'SETITEMS' and type(target) is dict and len(values) % 2 == 0:
                    for i in range(0, len(values), 2):
                        check_key(target, values[i])
                        target[values[i]] = values[i + 1]
                else: raise SeedSafetyError('malformed multidata container')
            elif code == 'APPEND':
                value = stack.pop()
                if type(stack[-1]) is not list: raise SeedSafetyError('malformed multidata list')
                stack[-1].append(value)
            elif code == 'SETITEM':
                value = stack.pop(); key = stack.pop()
                if type(stack[-1]) is not dict: raise SeedSafetyError('malformed multidata mapping')
                check_key(stack[-1], key)
                stack[-1][key] = value
            elif code == 'FROZENSET':
                values = pop_mark()
                for value in values: check_key(values, value)
                stack.append(frozenset(values))
            elif code == 'STACK_GLOBAL':
                name = stack.pop(); module = stack.pop(); stack.append(global_value(module, name))
            elif code == 'GLOBAL': stack.append(global_value(*arg.split(' ')))
            elif code in {'REDUCE', 'NEWOBJ'}:
                args = stack.pop(); constructor = stack.pop()
                if not isinstance(constructor, _Global) or type(args) is not tuple:
                    raise SeedSafetyError('unsupported multidata constructor')
                if constructor.name in ENUMS:
                    if len(args) != 1 or type(args[0]) is not int:
                        raise SeedSafetyError('malformed multidata enum')
                    stack.append(args[0])
                else: stack.append(args)
            elif code == 'STOP':
                if pos != len(raw) - 1 or len(stack) != 1 or type(stack[0]) is not dict:
                    raise SeedSafetyError('malformed multidata root or trailing data')
                return stack[0]
            else: raise SeedSafetyError('unsupported multidata pickle opcode')
    except SeedSafetyError:
        raise
    except Exception:
        raise SeedSafetyError('malformed multidata pickle') from None
    raise SeedSafetyError('incomplete multidata pickle')


def validate_multidata(data: bytes) -> None:
    if not data or data[0] != 3:
        raise SeedSafetyError('unsupported multidata format (expected format 3)')
    if len(data) > MAX_MULTIDATA:
        raise SeedSafetyError('compressed multidata size limit exceeded')
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(data[1:], MAX_MULTIDATA + 1)
        if len(raw) > MAX_MULTIDATA or decoder.unconsumed_tail:
            raise SeedSafetyError('expanded multidata size limit exceeded')
        if not decoder.eof or decoder.unused_data:
            raise SeedSafetyError('malformed multidata compression')
    except zlib.error:
        raise SeedSafetyError('malformed multidata compression') from None
    root = _data_pickle(raw)
    if type(root.get('server_options')) is not dict:
        raise SeedSafetyError('multidata missing server_options mapping')
    pending = [root]; visited = set()
    while pending:
        value = pending.pop()
        if id(value) in visited: continue
        visited.add(id(value))
        if type(value) is dict:
            for key, child in value.items():
                if isinstance(key, str) and key.casefold() in {'password', 'server_password'}:
                    if child is not None and child != '':
                        raise SeedSafetyError(f'multidata contains nonempty {key.casefold()} field')
                pending.append(child)
                pending.append(key)
        elif type(value) in {tuple, list, set, frozenset}: pending.extend(value)
        elif isinstance(value, _Global): raise SeedSafetyError('unsupported multidata global value')


def validate_seed_archive(path: Path, rom_extensions: set[str]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES or sum(e.file_size for e in entries) > MAX_ARCHIVE:
                raise SeedSafetyError('seed archive size or entry limit exceeded')
            seen = set(); multidata = 0
            for entry in entries:
                name = entry.filename.replace('\\', '/')
                parts = PurePosixPath(name).parts
                if name.startswith('/') or any(p in {'..'} or ':' in p for p in parts):
                    raise SeedSafetyError('seed archive contains an unsafe entry path')
                if name.casefold() in seen:
                    raise SeedSafetyError('seed archive contains duplicate entry paths')
                seen.add(name.casefold())
                if private_location(name, archive=True):
                    raise SeedSafetyError(f'seed archive contains credential/private-state entry: {name}')
                if PurePosixPath(name).suffix.lower() in rom_extensions:
                    raise SeedSafetyError(f'seed archive contains ROM-like entry: {name}')
                if entry.file_size > MAX_MEMBER:
                    raise SeedSafetyError(f'seed archive entry size limit exceeded: {name}')
                if entry.flag_bits & 1:
                    raise SeedSafetyError(f'seed archive contains encrypted entry: {name}')
                if name.lower().endswith('.archipelago'):
                    multidata += 1
                    if entry.file_size > MAX_MULTIDATA:
                        raise SeedSafetyError(f'multidata size limit exceeded: {name}')
                    try: validate_multidata(archive.read(entry))
                    except SeedSafetyError as exc: raise SeedSafetyError(f'{name}: {exc}') from None
                else:
                    with archive.open(entry) as stream:
                        while stream.read(1024 * 1024): pass  # CRC verification, bounded above.
            if multidata != 1:
                raise SeedSafetyError('seed archive must contain exactly one multidata file')
    except SeedSafetyError:
        raise
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, EOFError, zlib.error):
        raise SeedSafetyError('seed is not a readable, intact ZIP archive') from None
