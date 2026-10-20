import argparse
import contextlib
import importlib.machinery
import importlib.util
import io
import pathlib
import unittest
from unittest import mock


loader = importlib.machinery.SourceFileLoader("tflui", str(pathlib.Path(__file__).with_name("tflui")))
spec = importlib.util.spec_from_loader(loader.name, loader)
tflui = importlib.util.module_from_spec(spec)
loader.exec_module(tflui)


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.reservations = [
            {"job_id": "abc-123", "agent": "machine-one", "ipv4": "192.0.2.1"},
            {"job_id": "def-456", "agent": "machine-two", "ipv4": "192.0.2.2"},
        ]
        self.args = argparse.Namespace(
            software="juju", target="machine-two", user="ubuntu",
            script=tflui.DEFAULT_JUJU_SCRIPT,
        )
        self.run = self.enterContext(mock.patch.object(tflui.subprocess, "run"))
        self.run.return_value.returncode = 0
        self.enterContext(mock.patch.object(
            tflui, "get_active_reservations", return_value=self.reservations,
        ))
        self.open_script = self.enterContext(mock.patch.object(
            pathlib.Path, "open", mock.mock_open(read_data=b"#!/bin/bash\necho bootstrap\n"),
        ))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))

    def deploy(self, expected_code=0):
        with self.assertRaises(SystemExit) as raised:
            tflui.cmd_deploy(self.args)
        self.assertEqual(raised.exception.code, expected_code)

    def test_streams_local_script_to_selected_machine(self):
        self.deploy()
        self.open_script.assert_called_once_with("rb")
        command = self.run.call_args.args[0]
        self.assertEqual(command[0:2], ["ssh", "-T"])
        self.assertEqual(command[-2:], ["ubuntu@192.0.2.2", "sudo -n bash -s"])
        self.assertIs(self.run.call_args.kwargs["stdin"], self.open_script.return_value)
        self.assertFalse(self.run.call_args.kwargs["check"])

    def test_matches_job_prefix(self):
        self.args.target = "abc"
        self.deploy()
        self.assertEqual(self.run.call_args.args[0][-2], "ubuntu@192.0.2.1")

    def test_uses_only_reservation_when_target_omitted(self):
        self.reservations.pop()
        self.args.target = None
        self.deploy()
        self.assertEqual(self.run.call_args.args[0][-2], "ubuntu@192.0.2.1")

    def test_rejects_missing_or_ambiguous_target(self):
        for target in (None, "machine", "missing"):
            with self.subTest(target=target):
                self.args.target = target
                self.deploy(1)
        self.run.assert_not_called()

    def test_rejects_no_reservations(self):
        self.reservations.clear()
        self.deploy(1)
        self.run.assert_not_called()

    def test_rejects_missing_ip(self):
        for address in (None, "", "-"):
            with self.subTest(address=address):
                self.reservations[1]["ipv4"] = address
                self.deploy(1)
        self.run.assert_not_called()

    def test_reports_unreadable_script(self):
        self.open_script.side_effect = FileNotFoundError("missing bootstrap script")
        self.deploy(1)
        self.run.assert_not_called()

    def test_propagates_remote_failure(self):
        self.run.return_value.returncode = 42
        self.deploy(42)

    def test_reports_missing_ssh(self):
        self.run.side_effect = FileNotFoundError("ssh")
        self.deploy(1)

    def test_parser_accepts_script_and_user_overrides(self):
        with mock.patch.object(tflui.sys, "argv", [
            "tflui", "deploy", "juju", "abc", "--script", "/tmp/bootstrap.sh", "-u", "admin",
        ]), mock.patch.object(tflui, "cmd_deploy") as deploy:
            tflui.main()
        parsed = deploy.call_args.args[0]
        self.assertEqual((parsed.software, parsed.target), ("juju", "abc"))
        self.assertEqual((parsed.script, parsed.user), ("/tmp/bootstrap.sh", "admin"))


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.args = argparse.Namespace(
            interactive=False, queue="support-team", machine=None,
            distro="noble", lease="14d", timeout=tflui.DEFAULT_TIMEOUT,
            key=["lp:tester"], ephemeral=False, dry_run=True,
        )
        self.run = self.enterContext(mock.patch.object(tflui.subprocess, "run"))
        self.run.return_value.returncode = 0
        self.stderr = self.enterContext(contextlib.redirect_stderr(io.StringIO()))

    def launch(self):
        with self.assertRaises(SystemExit) as raised:
            tflui.cmd_launch(self.args)
        self.assertEqual(raised.exception.code, 0)
        command = self.run.call_args.args[0]
        return int(command[command.index("--timeout") + 1])

    def test_fourteen_days_uses_safe_support_team_timeout(self):
        self.assertEqual(tflui.parse_duration("14d"), 1209600)
        self.assertEqual(self.launch(), 1206900)
        self.assertIn("using 13d23h15m (1206900 seconds) instead", self.stderr.getvalue())

    def test_shorter_lease_is_unchanged(self):
        self.args.lease = "13d"
        self.assertEqual(self.launch(), 1123200)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_safe_limit_is_unchanged(self):
        self.args.lease = "13d23h15m"
        self.assertEqual(self.launch(), 1206900)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_other_queue_is_not_limited(self):
        self.args.queue = "another-queue"
        self.assertEqual(self.launch(), 1209600)
        self.assertEqual(self.stderr.getvalue(), "")

    def test_specific_machine_keeps_support_team_limit(self):
        self.args.machine = "machine-one"
        self.assertEqual(self.launch(), 1206900)
        self.assertIn("machine-one", self.run.call_args.args[0])

    def test_explicit_timeout_is_also_limited(self):
        self.args.lease = None
        self.args.timeout = 1209600
        self.assertEqual(self.launch(), 1206900)

    def test_interactive_summary_uses_adjusted_timeout(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        with mock.patch.object(tflui, "prompt_value", side_effect=[
            "support-team", "noble", "14d", "lp:tester",
        ]), mock.patch.object(tflui, "choose_machine", return_value=None), mock.patch.object(
            tflui, "prompt_yes_no", side_effect=[False, True],
        ):
            tflui.interactive_launch(self.args)
        self.assertIn("Lease time: 13d23h15m", tflui.sys.stdout.getvalue())
        self.assertIn("using 13d23h15m", self.stderr.getvalue())


if __name__ == "__main__":
    unittest.main()