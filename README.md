# tflui

A small wrapper around [testflinger-cli](https://testflinger.readthedocs.io/)
for people who juggle multiple active testflinger reservations.

## Commands

- `tflui list` (or just `tflui`) - list your active testflinger reservations
  in an `lxc list`-style table: job id, state, agent, device IP, and time
  left on the reservation lease.
- `tflui ssh [target]` - ssh into a reserved device. `target` matches a job
  id (or prefix) or agent name; if omitted and you only have one active
  reservation, that one is used. Extra args after `--` are passed to `ssh`
  (e.g. to run a remote command instead of an interactive shell).
- `tflui add-token` - store your personal testflinger client-id/secret-key
  (prompts securely if not passed via `--client-id`/`--secret-key`). This
  delegates to `testflinger-cli login`, so each user authenticates with
  their own credentials instead of a shared secret.
- `tflui token-status` - show which client id currently has a token stored.

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

For the support-team queue, use the `support-team` queue and the
corresponding secret key.

## Requirements

- Python 3
- `testflinger-cli` (installed and configured, e.g. via `snap install testflinger-cli`)
