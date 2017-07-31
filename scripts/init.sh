#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/../ && pwd )"
export PYTHONPATH="${PYTHONPATH}:${DIR}"
VENV_DIR=${DIR}/.venv

action_init ()
{
    . ${VENV_DIR}/bin/activate
}

### Main

action_init