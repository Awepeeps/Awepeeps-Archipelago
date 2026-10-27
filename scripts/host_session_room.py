"""Host a generated run as an archipelago.gg room under the stored admin session."""

from __future__ import annotations

import argparse
import http.cookiejar
import io
import json
import os
import re
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import (
    HTTPCookieProcessor,
    HTTPRedirectHandler,
    Request,
    build_opener,
)


ROOT = Path(__file__).resolve().parents[1]
SEED_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_seed\.zip$")
SPOILER_SUFFIX = "_Spoiler.txt"
ARCHIPELAGO_SUFFIX = ".archipelago"
USER_AGENT = "Awepeeps-Archipelago host_session_room.py"
FLASH_PATTERN = re.compile(
    r'class="[^"]*(?:flash|alert)[^"]*"[^>]*>(.*?)</',
    re.IGNORECASE | re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


class HostError(RuntimeError):
    """A user-actionable hosting error."""


@dataclass
class Response:
    status: int
    headers: Message
    body: bytes
    url: str


class NoRedirect(HTTPRedirectHandler):
    """Keep 3xx responses so the Location header can be read."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Host a generated run as an archipelago.gg room owned by the admin "
            "session in .admin/session_id.env. Use --dry-run to check without uploading."
        )
    )
    parser.add_argument("--season", required=True, help="Season directory relative to the repository root.")
    parser.add_argument("--run", required=True, help="Run directory name under .secrets/hidden.")
    parser.add_argument(
        "--session-env",
        type=Path,
        default=ROOT / ".admin" / "session_id.env",
        help="Session env file holding SESSION_ID; defaults to .admin/session_id.env.",
    )
    parser.add_argument(
        "--host",
        default="https://archipelago.gg",
        help="Archipelago host; defaults to https://archipelago.gg.",
    )
    parser.add_argument(
        "--include-spoiler",
        action="store_true",
        help="Upload the original seed bytes including the spoiler entry.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Host again even when the run already has a room.json record.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run local checks and print the plan without network calls or writing files.",
    )
    return parser.parse_args()


def resolve_path(path: Path, base: Path = ROOT) -> Path:
    return path.expanduser().resolve() if path.is_absolute() else (base / path).resolve()


def resolve_run(season: Path, run: str) -> Path:
    hidden = (season / ".secrets" / "hidden").resolve()
    if not hidden.is_dir():
        raise HostError(f"season is missing .secrets/hidden/: {season}")
    candidate = Path(run)
    run_dir = candidate.resolve() if candidate.is_absolute() else (hidden / candidate).resolve()
    try:
        run_dir.relative_to(hidden)
    except ValueError as exc:
        raise HostError(f"--run must name a directory inside {hidden}") from exc
    if not run_dir.is_dir():
        raise HostError(f"run directory not found: {run_dir}")
    return run_dir


def find_seed(run_dir: Path) -> Path:
    seeds = sorted(path for path in run_dir.glob("*_seed.zip") if SEED_NAME.fullmatch(path.name))
    if len(seeds) != 1:
        raise HostError(
            f"run must contain exactly one YYYY-MM-DD_seed.zip: {run_dir} (found {len(seeds)})"
        )
    return seeds[0]


def inspect_seed(seed: Path) -> tuple[list[str], list[str]]:
    try:
        with zipfile.ZipFile(seed) as archive:
            broken_file = archive.testzip()
            if broken_file is not None:
                raise HostError(f"seed archive is corrupt: {seed} ({broken_file})")
            names = archive.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise HostError(f"seed is not a readable ZIP archive: {seed}: {exc}") from exc

    archipelago_entries = [name for name in names if name.endswith(ARCHIPELAGO_SUFFIX)]
    if len(archipelago_entries) != 1:
        raise HostError(
            f"seed archive must contain exactly one {ARCHIPELAGO_SUFFIX} entry: {seed} "
            f"(found {len(archipelago_entries)})"
        )
    spoiler_entries = [name for name in names if name.endswith(SPOILER_SUFFIX)]
    return archipelago_entries, spoiler_entries


def build_upload_bytes(seed: Path, include_spoiler: bool) -> bytes:
    if include_spoiler:
        return seed.read_bytes()
    buffer = io.BytesIO()
    with zipfile.ZipFile(seed) as source, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for entry in source.infolist():
            if entry.filename.endswith(SPOILER_SUFFIX):
                continue
            target.writestr(entry, source.read(entry))
    return buffer.getvalue()


def parse_session_env(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HostError(f"could not read session env file: {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise HostError(f"session env file is not UTF-8 text: {path}: {exc}") from exc

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    session_id = values.get("SESSION_ID")
    if not session_id:
        raise HostError(f"session env file does not define SESSION_ID: {path}")
    try:
        uuid.UUID(session_id)
    except ValueError as exc:
        raise HostError("SESSION_ID in the session env file is not a valid UUID") from exc
    return session_id


def mask_session(session_id: str) -> str:
    return session_id[:4] + "..."


def existing_room_url(room_record: Path) -> str:
    try:
        record = json.loads(room_record.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HostError(f"could not read existing room record {room_record}: {exc}") from exc
    room_url = record.get("room_url") if isinstance(record, dict) else None
    if not isinstance(room_url, str) or not room_url:
        raise HostError(f"existing room record is missing room_url: {room_record}")
    return room_url


def validate_host(host: str) -> tuple[str, str]:
    host = host.rstrip("/")
    parsed = urlsplit(host)
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise HostError("--host must be an http(s) URL with a hostname")
    if parsed.scheme == "http" and hostname.lower() not in {"localhost", "127.0.0.1", "::1"}:
        raise HostError("--host must use HTTPS unless the hostname is localhost, 127.0.0.1, or ::1")
    return host, hostname


def write_room_record(room_record: Path, record: dict) -> None:
    temporary = room_record.with_name(f".{room_record.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, room_record)
    except OSError as exc:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise HostError(f"could not write room record {room_record}: {exc}") from exc


def fetch(
    opener,
    url: str,
    *,
    label: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    request = Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
        method=method,
    )
    try:
        with opener.open(request) as response:
            return Response(response.status, response.headers, response.read(), response.geturl())
    except HTTPError as exc:
        return Response(exc.code, exc.headers, exc.read(), exc.geturl() or url)
    except (URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise HostError(f"{label} failed: {reason}") from exc


def location_path(headers: Message, base: str) -> str | None:
    location = headers.get("Location")
    if not location:
        return None
    return urlsplit(urljoin(base, location)).path


def flash_message(body: bytes, content_type: str) -> str | None:
    if "html" not in content_type.lower():
        return None
    text = body.decode("utf-8", errors="replace")
    for match in FLASH_PATTERN.finditer(text):
        cleaned = TAG_PATTERN.sub(" ", match.group(1))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            return cleaned
    return None


def build_multipart(filename: str, content: bytes, boundary: str) -> bytes:
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/zip\r\n"
        "\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + content + tail


def upload_seed(manual, host: str, seed_name: str, upload_bytes: bytes) -> str:
    boundary = uuid.uuid4().hex
    body = build_multipart(seed_name, upload_bytes, boundary)
    response = fetch(
        manual,
        f"{host}/uploads",
        label="uploading the seed",
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    if 300 <= response.status < 400:
        path = location_path(response.headers, f"{host}/uploads")
        match = re.fullmatch(r"/seed/([^/]+)/?", path or "")
        if match:
            return match.group(1)

    flash = flash_message(response.body, response.headers.get("Content-Type", ""))
    detail = f": {flash}" if flash else ""
    raise HostError(f"seed upload failed (HTTP {response.status}){detail}")


def create_room(manual, host: str, seed_id: str) -> str:
    response = fetch(manual, f"{host}/new_room/{seed_id}", label="creating the room")
    if 300 <= response.status < 400:
        path = location_path(response.headers, f"{host}/new_room/{seed_id}")
        match = re.fullmatch(r"/room/([^/]+)/?", path or "")
        if match:
            return match.group(1)

    flash = flash_message(response.body, response.headers.get("Content-Type", ""))
    detail = f": {flash}" if flash else ""
    raise HostError(f"room creation failed (HTTP {response.status}){detail}")


def read_room_page(follow, host: str, room_id: str, hostname: str) -> tuple[int, str]:
    response = fetch(follow, f"{host}/room/{room_id}", label="reading the room page")
    if not 200 <= response.status < 300:
        raise HostError(f"could not read the room page (HTTP {response.status})")
    page = response.body.decode("utf-8", errors="replace")

    port_match = re.search(rf"{re.escape(hostname)}:(\d+)", page)
    if port_match is None:
        raise HostError("could not find the room port on the room page")
    port = int(port_match.group(1))

    tracker_match = re.search(r"/tracker/([A-Za-z0-9_-]+)", page)
    if tracker_match is None:
        raise HostError("could not find the tracker id on the room page")
    tracker_url = f"{host}/tracker/{tracker_match.group(1)}"
    return port, tracker_url


def main() -> int:
    args = parse_args()
    try:
        season = resolve_path(Path(args.season))
        if not season.is_dir():
            raise HostError(f"season directory not found: {season}")

        host, hostname = validate_host(args.host)

        run_dir = resolve_run(season, args.run)
        room_record = run_dir / "room.json"
        if room_record.exists() and not args.force:
            print(f"Room already recorded for run {run_dir.name}: {room_record}")
            print(f"Room URL: {existing_room_url(room_record)}")
            try:
                prior_record = json.loads(room_record.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise HostError(f"could not read existing room record {room_record}: {exc}") from exc
            if not isinstance(prior_record, dict) or prior_record.get("complete") is not True:
                print("Room record is incomplete; the room exists but hosting did not finish.")
            print("Re-run with --force to create an additional room.")
            return 0

        seed = find_seed(run_dir)
        _, spoiler_entries = inspect_seed(seed)
        upload_bytes = build_upload_bytes(seed, args.include_spoiler)
        if args.include_spoiler:
            mode = f"original seed bytes, spoiler included ({len(spoiler_entries)} entry/entries)"
        else:
            mode = (
                "upload copy without spoiler entries "
                f"(removed {len(spoiler_entries)} from the archive)"
            )

        session_id = parse_session_env(resolve_path(args.session_env))
        masked = mask_session(session_id)

        print(f"Season: {season}")
        print(f"Run: {run_dir}")
        print(f"Seed: {seed}")
        print(f"Upload mode: {mode}")
        print(f"Host: {host}")
        print(f"Session: {masked}")
        print("Planned requests:")
        print(f"  1. GET {host}/session/{masked}  (sets the admin session cookie)")
        print(f"  2. POST {host}/uploads  (multipart field file={seed.name})")
        print(f"  3. GET {host}/new_room/<seed id from the upload redirect>")
        print(f"  4. GET {host}/room/<room id from the new_room redirect>")
        if args.dry_run:
            print("Dry run complete; no network calls were made and no files were written.")
            return 0

        cookie_jar = http.cookiejar.CookieJar()
        follow = build_opener(HTTPCookieProcessor(cookie_jar))
        manual = build_opener(NoRedirect(), HTTPCookieProcessor(cookie_jar))

        session_response = fetch(
            follow,
            f"{host}/session/{session_id}",
            label="opening the admin session page",
        )
        if not 200 <= session_response.status < 400:
            raise HostError(
                f"could not open the admin session page (HTTP {session_response.status}); "
                "confirm the SESSION_ID in the env file"
            )

        seed_id = upload_seed(manual, host, seed.name, upload_bytes)
        seed_url = f"{host}/seed/{seed_id}"
        room_id = create_room(manual, host, seed_id)
        room_url = f"{host}/room/{room_id}"
        record = {
            "run": run_dir.name,
            "seed_file": seed.name,
            "spoiler_uploaded": bool(args.include_spoiler),
            "host": host,
            "seed_url": seed_url,
            "room_url": room_url,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tracker_url": None,
            "port": None,
            "complete": False,
        }
        try:
            write_room_record(room_record, record)
        except HostError as exc:
            print(f"Room URL: {room_url}")
            raise HostError(f"room exists, but its partial record could not be saved: {exc}") from exc
        try:
            port, tracker_url = read_room_page(follow, host, room_id, hostname)
        except HostError as exc:
            print(f"Room URL: {room_url}")
            raise HostError(f"room exists, but its page could not be read; partial record kept: {exc}") from exc
        record.update({"tracker_url": tracker_url, "port": port, "complete": True})
        write_room_record(room_record, record)

        print(f"Seed URL: {seed_url}")
        print(f"Room URL: {room_url}")
        print(f"Tracker URL: {tracker_url}")
        print(f"Server: {hostname}:{port}")
        print(f"Room record: {room_record}")
        print(
            "Note: the port only holds while the room is running; archipelago.gg assigns a "
            "new port each time an idle room restarts."
        )
        print(
            "Point the bridgeipelago bot (docs/discord-bot.md) at this room by updating "
            "ArchipelagoPort, ArchipelagoTrackerURL, ArchipelagoServerURL, and UniqueID."
        )
        return 0
    except HostError as exc:
        print(f"Hosting failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
