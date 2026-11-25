import fcntl
from pathlib import Path
import json
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/sync-channel.py"))
SYNC = MODULE["synchronize"].__globals__


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.settings = patch.dict(SYNC, STATE=self.state)
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def staged(self):
        stage = self.state / "stage"
        stage.mkdir()
        (stage / "channel.payload").write_bytes(b"verified snapshot")
        return stage

    def test_expired_snapshot_keeps_current(self):
        current = self.state / "current"
        current.symlink_to("snapshot-1-publish-abcdefgh")
        with patch.object(SYNC["time"], "time", return_value=20):
            with self.assertRaisesRegex(ValueError, "expired"):
                SYNC["activate"](self.staged(), {"issued": 10, "expires": 20, "sequence": 2})
        self.assertEqual(os.readlink(current), "snapshot-1-publish-abcdefgh")

    def test_rename_failure_keeps_current(self):
        current = self.state / "current"
        current.symlink_to("snapshot-1-publish-abcdefgh")
        with patch.object(SYNC["time"], "time", return_value=19), patch.object(
            Path, "replace", side_effect=OSError("interrupted before commit")
        ):
            with self.assertRaises(OSError):
                SYNC["activate"](self.staged(), {"issued": 10, "expires": 20, "sequence": 2})
        self.assertEqual(os.readlink(current), "snapshot-1-publish-abcdefgh")

    def test_activation_points_to_complete_relative_snapshot(self):
        with patch.object(SYNC["time"], "time", return_value=19):
            SYNC["activate"](self.staged(), {"issued": 10, "expires": 20, "sequence": 2})
        current = self.state / "current"
        self.assertRegex(os.readlink(current), r"^snapshot-2-publish-[a-z0-9_]{8}$")
        self.assertEqual((current / "channel.payload").read_bytes(), b"verified snapshot")

    def test_reject_external_pointer_before_read(self):
        (self.state / "current").symlink_to("../outside")
        with patch.dict(SYNC, read_channel=lambda _: ({}, "")):
            with self.assertRaisesRegex(ValueError, "pointer"):
                SYNC["synchronize"]()

    def test_same_sequence_requires_identical_payload(self):
        saved = {"version": "1.0.0beta29_2", "sequence": 1, "expires": 20}
        old = self.state / "snapshot-1-publish-abcdefgh"
        old.mkdir()
        (old / "channel.payload").write_text(json.dumps(saved))
        (self.state / "current").symlink_to(old.name)
        updated = dict(saved, expires=21)

        def read_channel(stage):
            (stage / "channel.payload").write_text(json.dumps(updated))
            return updated, ""

        with patch.dict(SYNC,
            read_channel=read_channel, trusted_directory=lambda *_a, **_k: None,
            safe_regular=lambda path, name, flags: os.open(path / name, flags),
            compare=lambda *_: 0,
        ):
            with self.assertRaisesRegex(ValueError, "Conflicting payload"):
                SYNC["synchronize"]()

    def test_unsafe_file_types_are_rejected(self):
        target = self.state / "target"
        target.write_text("kept intact")
        (self.state / "link").symlink_to(target)
        os.link(target, self.state / "hardlink")
        os.mkfifo(self.state / "pipe")
        for name in ("link", "hardlink", "pipe"):
            with self.subTest(name=name), self.assertRaises((OSError, ValueError)):
                fd = SYNC["safe_regular"](self.state, name, os.O_RDONLY)
                os.close(fd)
        self.assertEqual(target.read_text(), "kept intact")

    def test_process_lock_serializes_writers(self):
        script = """
import fcntl, sys
with open(sys.argv[1], "w") as file:
    try:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(13)
"""
        path = self.state / "lock"
        with path.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            blocked = subprocess.run([sys.executable, "-I", "-c", script, str(path)], check=False)
            self.assertEqual(blocked.returncode, 13)
        released = subprocess.run([sys.executable, "-I", "-c", script, str(path)], check=False)
        self.assertEqual(released.returncode, 0)

    def test_short_download_is_rejected(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = {"Content-Length": "12"}
        response.read1.side_effect = (b"abc", b"")
        opener = MagicMock()
        opener.open.return_value = response
        with patch.dict(SYNC, build_opener=lambda *_: opener):
            with self.assertRaisesRegex(ValueError, "Incomplete download"):
                SYNC["fetch"]("https://example.invalid/index", self.state / "index", 12)

    def test_elapsed_download_deadline_is_rejected(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = {}
        response.read1.return_value = b"abc"
        opener = MagicMock()
        opener.open.return_value = response
        with patch.dict(SYNC, build_opener=lambda *_: opener), patch.object(
            SYNC["time"], "monotonic", side_effect=(0, 301)
        ):
            with self.assertRaisesRegex(ValueError, "limit exceeded"):
                SYNC["fetch"]("https://example.invalid/index", self.state / "index", 12)

    def test_reject_writable_or_symlink_ancestor(self):
        path = Path("/var/lib/test")
        for kind in (stat.S_IFDIR | 0o777, stat.S_IFLNK | 0o777):
            def lstat(directory):
                mode = kind if directory == path.parent else stat.S_IFDIR | 0o755
                return os.stat_result((mode, 0, 0, 1, 0, 0, 0, 0, 0, 0))
            with self.subTest(kind=kind), patch.object(Path, "lstat", lstat):
                with self.assertRaisesRegex(ValueError, "root-owned"):
                    SYNC["trusted_directory"](path)


if __name__ == "__main__":
    unittest.main()
