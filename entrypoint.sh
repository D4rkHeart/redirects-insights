#!/bin/bash
set -e

if [ -z "$SSH_AUTH_SOCK" ]; then
  echo "Erreur : SSH_AUTH_SOCK n'est pas défini."
  exit 1
fi

if [ ! -S "$SSH_AUTH_SOCK" ]; then
  echo "Erreur : le socket SSH $SSH_AUTH_SOCK n'existe pas."
  exit 1
fi

socat UNIX-LISTEN:/tmp/ssh-agent.sock,fork UNIX-CONNECT:$SSH_AUTH_SOCK &

export SSH_AUTH_SOCK=/tmp/ssh-agent.sock

sleep 1

exec python ./scripts/analyze_redirects.py
