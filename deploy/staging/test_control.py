"""Safety regression tests; no Docker or VPS required."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("staging_control", Path(__file__).with_name("control.py"))
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def valid_env():
    return "\n".join(["STAGING_DB_PASSWORD=" + "a" * 64, "STAGING_RELEASE_SHA=" + "b" * 40]
                     + [f"STAGING_{name}_IMAGE=example/image@sha256:" + "c" * 64
                        for name in ("API", "GATEWAY", "FRONTEND", "DB", "REDIS", "PROXY")])


class Guards(unittest.TestCase):
    def test_valid_digest_manifest(self):
        self.assertEqual(len(control.values(valid_env())), 8)

    def test_rejects_tags_and_external_database_override(self):
        for text in (valid_env().replace("@sha256:" + "c" * 64, ":latest"),
                     valid_env() + "\nDATABASE_URL=postgresql://production",
                     valid_env() + "\nSTAGING_DB_PASSWORD=duplicate"):
            with self.assertRaises(RuntimeError):
                control.values(text)

    def test_foreign_container_blocks(self):
        with patch.object(control, "run", side_effect=["container", json.dumps([
            {"Config": {"Labels": {"com.docker.compose.project": "production"}}}])]):
            with self.assertRaisesRegex(RuntimeError, "Foreign container"):
                control.inventory()

    def test_foreign_volume_blocks(self):
        with patch.object(control, "run", side_effect=["", "volume", json.dumps([
            {"Name": "production_data", "Labels": {}}])]):
            with self.assertRaisesRegex(RuntimeError, "Foreign/externally"):
                control.inventory()

    def test_external_driver_options_block(self):
        volume = {"Name": "mihur-staging_database", "Driver": "local",
                  "Labels": {"com.docker.compose.project": "mihur-staging"},
                  "Options": {"type": "nfs", "device": ":/production"}}
        with patch.object(control, "run", side_effect=["", "volume", json.dumps([volume])]):
            with self.assertRaises(RuntimeError):
                control.inventory()

    def test_empty_inventory_allowed(self):
        with patch.object(control, "run", side_effect=["", ""]):
            control.inventory()

    def test_arbitrary_action_blocked_before_preflight(self):
        with patch.object(control.sys, "argv", ["control.py", "down"]), \
                patch.object(control, "preflight") as preflight:
            with self.assertRaises(RuntimeError):
                control.main()
            preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
