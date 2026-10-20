# tflui

A small wrapper around [testflinger-cli](https://testflinger.readthedocs.io/)
for people who juggle multiple active testflinger reservations.

## Commands

- `tflui list` (or just `tflui`) - list your active testflinger reservations
  in an `lxc list`-style table: job id, state, agent, device IP, and time
  left on the reservation lease.
- `tflui machines [-q QUEUE] [--all]` - list available machines in a
  testflinger queue. Use `--all` to include busy and unavailable machines.
- `tflui launch` - launch a reserved testflinger instance. When run without
  flags in an interactive terminal, prompts for queue, machine, distro, lease,
  SSH key, and ephemeral deployment. Use `--no-interactive` to use defaults
  and flags only.
- `tflui ssh [target]` - ssh into a reserved device. `target` matches a job
  id (or prefix) or agent name; if omitted and you only have one active
  reservation, that one is used. Extra args after `--` are passed to `ssh`
  (e.g. to run a remote command instead of an interactive shell).
- `tflui deploy juju [target]` - deploy Juju on an already-launched reserved
  device using the local bastion bootstrap script. Target selection works
  like `ssh`; omit the target only when one reservation is active.
- `tflui release [target]` - release a reserved device early. `target` matches
  a job id (or prefix) or agent name; if omitted and you only have one active
  reservation, that one is used. Use `-y`/`--yes` to skip confirmation.
- `tflui add-token` - store your personal testflinger client-id/secret-key
  (prompts securely if not passed via `--client-id`/`--secret-key`). This
  delegates to `testflinger-cli login`, so each user authenticates with
  their own credentials instead of a shared secret. Credentials are saved for
  future CLI authentication so the six-day refresh-token expiry does not
  require running `add-token` again.
- `tflui token-status` - show which client id currently has a token stored.

## Launch options

`launch` supports:

- `-q`, `--queue` - queue name
- `-m`, `--machine` - specific machine to reserve, or `random`
- `--distro` - distro to provision
- `--timeout` - reservation timeout in seconds
- `--lease` - human-friendly lease time, e.g. `2h`, `1d`, `14d`
- `-k`, `--key` - SSH key to inject, e.g. `lp:userid` or `gh:userid`
- `--ephemeral` - use a MAAS ephemeral deployment
- `--dry-run` - print the job data without submitting
- `--no-interactive` - use defaults/flags without prompts

Defaults can be overridden with `TFLUI_QUEUE`, `TFLUI_DISTRO`, `TFLUI_TIMEOUT`,
`TFLUI_LEASE`, and `TFLUI_KEY`.

The default lease is `13d23h15m` (`1206900` seconds). For `support-team`,
longer requests (including `--lease 14d` or an explicit `--timeout`) are
shortened to this conservative limit with a warning: a full 14 days is
`1209600` seconds and can be rejected by the server's reservation permissions.
This limit also applies when selecting a specific machine with `--machine`
under `--queue support-team`. Other queues retain the requested duration;
their limits are enforced by the server.

## Deploy Juju

After launching a machine and waiting for it to appear in `tflui list` as
reserved, deploy to its agent name or job id (prefixes are accepted):

```sh
tflui deploy juju machine-name
```

The command reads `~/lab/testflinger/bastion-bootstrap.sh` on your local
machine and streams it over SSH to `sudo -n bash -s` on the selected device.
The script installs Juju and LXD and bootstraps a local LXD cloud controller
named `bastion-controller` for the remote `ubuntu` user. It must exist locally;
it does not need to be copied to the device first.

The SSH user defaults to `ubuntu` and must have passwordless sudo access.
The bootstrap script also requires the remote `ubuntu` account to exist,
even when using a different SSH user. Override the local script or SSH user
when needed:

```sh
tflui deploy juju machine-name --script /path/to/bootstrap.sh --user ubuntu
```

Deployment output streams to your terminal, and SSH or bootstrap failures
produce a nonzero exit status. Deployment is explicit: `launch` does not
automatically run the bootstrap script.

## Install

1. Clone the repo:
   ```sh
   git clone https://github.com/rmolkentin/tflui && cd tflui
   ```
2. Make it executable and link it onto your `PATH`:
   ```sh
   chmod +x tflui
   mkdir -p ~/bin
   ln -s "$(pwd)/tflui" ~/bin/tflui
   ```

Then authenticate once with your own testflinger credentials:

```sh
tflui add-token
```

The client ID and secret key are stored in
`$XDG_CONFIG_HOME/tflui/credentials.conf`
(default: `~/.config/tflui/credentials.conf`) with owner-only permissions.
The file contains plaintext credentials, so protect access to your user
account and delete the file to remove the saved credentials.

For the support-team queue, use the client ID `support-team` and the
corresponding secret key.

## Requirements

- Python 3
- `testflinger-cli` (installed and configured, e.g. via `snap install testflinger-cli`)
- OpenSSH client for `ssh` and `deploy`
