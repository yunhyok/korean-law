import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("installer", Path(__file__).resolve().parents[1] / "scripts/install_skill.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_dry_run_idempotence_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source, destination = Path(temp) / "source", Path(temp) / "skills/law"
            source.mkdir()
            (source / "SKILL.md").write_text("original", encoding="utf-8")
            (source / "build.egg-info").mkdir()
            (source / "build.egg-info/PKG-INFO").write_text("build metadata", encoding="utf-8")
            installer.install(source, destination, dry_run=True)
            self.assertFalse(destination.exists())
            installer.install(source, destination)
            self.assertEqual(installer.files(source), installer.files(destination))
            self.assertFalse((destination / "build.egg-info").exists())
            self.assertIn("Already installed", installer.install(source, destination))
            (destination / "SKILL.md").write_text("user edit", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install(source, destination)
            self.assertEqual((destination / "SKILL.md").read_text(), "user edit")
