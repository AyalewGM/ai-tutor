"""Safety regression tests; no Docker or VPS required."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "staging_control", Path(__file__).with_name("control.py")
)
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def valid_env():
    return "\n".join(
        ["STAGING_DB_PASSWORD=" + "a" * 64, "STAGING_RELEASE_SHA=" + "b" * 40]
        + [
            f"STAGING_{name}_IMAGE=example/image@sha256:" + "c" * 64
            for name in ("API", "GATEWAY", "FRONTEND", "DB", "REDIS", "PROXY")
        ]
    )


class Guards(unittest.TestCase):
    def test_valid_digest_manifest(self):
        self.assertEqual(len(control.values(valid_env())), 8)

    def test_rejects_tags_and_external_database_override(self):
        for text in (
            valid_env().replace("@sha256:" + "c" * 64, ":latest"),
            valid_env() + "\nDATABASE_URL=postgresql://production",
            valid_env() + "\nSTAGING_DB_PASSWORD=duplicate",
        ):
            with self.assertRaises(RuntimeError):
                control.values(text)

    def test_foreign_container_blocks(self):
        with (
            patch.object(
                control,
                "run",
                side_effect=[
                    "container",
                    json.dumps(
                        [{"Config": {"Labels": {"com.docker.compose.project": "production"}}}]
                    ),
                ],
            ),
            self.assertRaisesRegex(RuntimeError, "Foreign container"),
        ):
            control.inventory()

    def test_foreign_volume_blocks(self):
        with (
            patch.object(
                control,
                "run",
                side_effect=["", "volume", json.dumps([{"Name": "production_data", "Labels": {}}])],
            ),
            self.assertRaisesRegex(RuntimeError, "Foreign/externally"),
        ):
            control.inventory()

    def test_external_driver_options_block(self):
        volume = {
            "Name": "mihur-staging_database",
            "Driver": "local",
            "Labels": {"com.docker.compose.project": "mihur-staging"},
            "Options": {"type": "nfs", "device": ":/production"},
        }
        with (
            patch.object(control, "run", side_effect=["", "volume", json.dumps([volume])]),
            self.assertRaises(RuntimeError),
        ):
            control.inventory()

    def test_named_redis_volume_allowed(self):
        labels = {"com.docker.compose.project": "mihur-staging"}
        container = {"Config": {"Labels": labels}, "Mounts": [
            {"Type": "volume", "Name": "mihur-staging_redis_data"}
        ]}
        volume = {"Name": "mihur-staging_redis_data", "Labels": labels,
                  "Driver": "local", "Options": None}
        with patch.object(control, "run", side_effect=[
            "redis", json.dumps([container]), "volume", json.dumps([volume]), ""
        ]):
            control.inventory()

    def test_anonymous_redis_volume_still_rejected(self):
        container = {"Config": {"Labels": {
            "com.docker.compose.project": "mihur-staging"
        }}, "Mounts": [{"Type": "volume", "Name": "1a9d23"}]}
        with (
            patch.object(control, "run", side_effect=["redis", json.dumps([container])]),
            self.assertRaisesRegex(RuntimeError, "Unexpected container volume"),
        ):
            control.inventory()

    def test_review_policy_mount_allowed_only_for_api_and_migrate(self):
        for service in ("tutor-api", "migrate"):
            with self.subTest(service=service):
                container = self.bind_container(service, {
                    "Type": "bind", "Source": "/etc/mihur-staging/content-review-policy.json",
                    "Destination": "/run/mihur/content-review-policy.json", "RW": False,
                })
                with patch.object(control, "run", side_effect=[
                    "synthetic-id", json.dumps([container]), "", "",
                ]):
                    control.inventory()

    @staticmethod
    def bind_container(service, mount):
        return {"Id": "synthetic-id", "Config": {"Labels": {
            "com.docker.compose.project": "mihur-staging",
            "com.docker.compose.service": service,
        }}, "Mounts": [mount]}

    def test_review_policy_mount_mismatches_are_rejected(self):
        valid = {"Type": "bind", "Source": "/etc/mihur-staging/content-review-policy.json",
                 "Destination": "/run/mihur/content-review-policy.json", "RW": False}
        cases = [
            ("tutor-api", {**valid, "Source": "/etc/other-policy.json"}),
            ("migrate", {**valid, "Destination": "/etc/mihur/policy.json"}),
            ("tutor-api", {**valid, "RW": True}),
            ("migrate", {**valid, "RW": "false"}),
            ("proxy", valid), ("frontend", valid), (None, valid),
            ("tutor-api", {**valid, "Type": "tmpfs"}),
        ]
        for service, mount in cases:
            with self.subTest(service=service, mount=mount):
                with (
                    patch.object(control, "run", side_effect=[
                        "synthetic-id", json.dumps([self.bind_container(service, mount)]),
                    ]),
                    self.assertRaisesRegex(RuntimeError, "Unexpected bind mount"),
                ):
                    control.inventory()

    def test_caddy_bind_remains_exact_readonly_and_proxy_only(self):
        valid = {"Type": "bind", "Source": str(control.CONFIG.parent / "Caddyfile"),
                 "Destination": "/etc/caddy/Caddyfile", "RW": False}
        with patch.object(control, "run", side_effect=[
            "synthetic-id", json.dumps([self.bind_container("proxy", valid)]), "", "",
        ]):
            control.inventory()
        for service, mount in [
            ("tutor-api", valid),
            ("proxy", {**valid, "Destination": "/run/mihur/content-review-policy.json"}),
            ("proxy", {**valid, "Source": "/etc/foreign/Caddyfile"}),
            ("proxy", {**valid, "RW": True}),
        ]:
            with self.subTest(service=service, mount=mount):
                with (
                    patch.object(control, "run", side_effect=[
                        "synthetic-id", json.dumps([self.bind_container(service, mount)]),
                    ]),
                    self.assertRaisesRegex(RuntimeError, "Unexpected bind mount"),
                ):
                    control.inventory()

    def test_edge_network_scope(self):
        edge = {"Name": "mihur-staging_edge", "Driver": "bridge", "Internal": False,
                "Options": {"com.docker.network.bridge.host_binding_ipv4": "127.0.0.1"},
                "Containers": {"proxy-id": {}}}
        self.assertTrue(control.valid_edge_network(edge, {"proxy-id"}))
        self.assertFalse(control.valid_edge_network(edge, set()))
        for field, bad in [("Driver", "overlay"), ("Internal", True),
                           ("Name", "foreign"), ("Options", {})]:
            with self.subTest(field=field):
                self.assertFalse(control.valid_edge_network({**edge, field: bad}, {"proxy-id"}))

    def test_application_cannot_attach_edge(self):
        item = {"Config": {"Labels": {
            "com.docker.compose.project": "mihur-staging",
            "com.docker.compose.service": "tutor-api",
        }}, "NetworkSettings": {"Networks": {"mihur-staging_edge": {}}}}
        with (
            patch.object(control, "run", side_effect=["api", json.dumps([item])]),
            self.assertRaisesRegex(RuntimeError, "network attachment"),
        ):
            control.inventory()

    def test_empty_inventory_allowed(self):
        with patch.object(control, "run", side_effect=["", "", ""]):
            control.inventory()

    def test_non_internal_network_blocks(self):
        network = {
            "Name": "mihur-staging_staging",
            "Internal": False,
            "Labels": {"com.docker.compose.project": "mihur-staging"},
        }
        with (
            patch.object(control, "run", side_effect=["", "", "network", json.dumps([network])]),
            self.assertRaisesRegex(RuntimeError, "non-isolated"),
        ):
            control.inventory()

    def test_arbitrary_action_blocked_before_preflight(self):
        with (
            patch.object(control.sys, "argv", ["control.py", "down"]),
            patch.object(control, "preflight") as preflight,
        ):
            with self.assertRaises(RuntimeError):
                control.main()
            preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
