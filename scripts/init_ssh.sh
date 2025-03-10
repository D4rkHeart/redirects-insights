#!/bin/bash
set -e

if [ -z "$SSH_AUTH_SOCK" ]; then
  eval $(ssh-agent -s)
fi

if ! ssh-add -l | grep -q "id_ed25519"; then
  ssh-add ~/.ssh/id_ed25519
fi

export SSH_AUTH_SOCK

docker-compose up --build
