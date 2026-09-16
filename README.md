# tflui

A small wrapper around [testflinger-cli](https://testflinger.readthedocs.io/)
for people who juggle multiple active testflinger reservations.

## Commands

- `tflui list` (or just `tflui`) — list your active testflinger reservations
  in an `lxc list`-style table: job id, state, agent, device IP, and time
  left on the reservation lease.
- `tflui ssh [target]` — ssh into a reserved device. `target` matches a job
  id (or prefix) or agent name; if omitted and you only have one active
  reservation, that one is used. Extra args after `--` are passed to `ssh`
  (e.g. to run a remote command instead of an interactive shell).
- `tflui add-token` — store your personal testflinger client-id/secret-key
  (prompts securely if not passed via `--client-id`/`--secret-key`). This
  delegates to `testflinger-cli login`, so each user authenticates with
  their own credentials instead of a shared secret.
- `tflui token-status` — show which client id currently has a token stored.

## Install

```sh
chmod +x tflui
ln -s "$(pwd)/tflui" ~/bin/tflui   # or anywhere on your PATH
```

## Requirements

- Python 3
- `testflinger-cli` (installed and configured, e.g. via `snap install testflinger-cli`)
