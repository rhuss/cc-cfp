#!/bin/sh
# Seed a fictional cfp store for the paste-view visual (no network access).
# Runs inside the cfp CLI container; visuals/ is mounted read-only at /visuals.
set -eu

cfp() {
  python3 -I /opt/cfp/scripts/cfp_store.py "$@" --store /tmp/store --today 2026-10-01
}

cfp config init --speaker-name "Ada Example" --speaker-company "Example Corp" \
  --seed-dir /opt/cfp/knowledge-base/profiles
cfp talk write --from-json /visuals/seed/talk.json
cfp proposal create --talk safe-node-drains --profile kubecon --event kubecon-eu-2027 \
  --session-type session
for field in title abstract value_to_community; do
  cfp proposal set-field --proposal kubecon-eu-2027--safe-node-drains --field "$field" \
    --text-file "/visuals/seed/$field.txt"
done
