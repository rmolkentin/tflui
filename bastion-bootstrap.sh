#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root or with sudo." >&2
  exit 1
fi

LXD_TRUST_PASSWORD="${LXD_TRUST_PASSWORD:-bastion-trust-password}"
CONTROLLER_NAME="${CONTROLLER_NAME:-bastion-controller}"

apt-get update
apt-get install -y ca-certificates curl jq snapd

snap wait system seed.loaded || true
snap install juju --classic --channel=3.6/stable || snap install juju --classic
snap install lxd --channel=5.21/stable || snap install lxd

lxd init --auto || true
lxc config set core.trust_password "$LXD_TRUST_PASSWORD"

cat > /tmp/bastion-cloud.yaml <<YAML
clouds:
  lxd:
    type: lxd
    auth-types: [certificate]
    endpoint: https://127.0.0.1:8443
    regions:
      default:
        endpoint: https://127.0.0.1:8443
YAML

cat > /tmp/bastion-credentials.yaml <<YAML
credentials:
  lxd:
    bastion:
      auth-type: interactive
      trust-password: "$LXD_TRUST_PASSWORD"
YAML

install -d -o ubuntu -g ubuntu -m 700 /home/ubuntu/.local/share/juju

sudo -H -u ubuntu env HOME=/home/ubuntu PATH=/snap/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin CONTROLLER_NAME="${CONTROLLER_NAME}" bash -c '
set -euxo pipefail
export PATH=/snap/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/home/ubuntu
mkdir -p "$HOME/.local/share/juju"

juju add-cloud lxd /tmp/bastion-cloud.yaml --client || true
juju add-credential lxd -f /tmp/bastion-credentials.yaml --client || true
juju bootstrap lxd "${CONTROLLER_NAME}" --debug --bootstrap-series=noble
'

echo "done: ${CONTROLLER_NAME}"