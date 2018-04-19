#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/../ && pwd )"
export PYTHONPATH="${PYTHONPATH}:${DIR}"
VENV_DIR=${DIR}/.venv

action_prepare ()
{
    . ${VENV_DIR}/bin/activate
    pip install awscli
    pip install boto3
    pip install troposphere
    pip install awacs
    pip install executor
    pip install click
    pip install requests 2>&1 > /dev/null
    #pip install netifaces 2>&1 > /dev/null
    #pip install pyyaml 2>&1 > /dev/null
    #pip install psutil 2>&1 > /dev/null
    #pip install numpy 2>&1 > /dev/null
    #pip install scipy 2>&1 > /dev/null
    #pip install scikit-learn 2>&1 > /dev/null
    #pip install pandas 2>&1 > /dev/null
    pip install --editable ${DIR} 2>&1 #> /dev/null
    deactivate
}


action_init ()
{
    if [ ! -d "$VENV_DIR" ]; then
        virtualenv $VENV_DIR
    fi
    action_prepare
}

### Main

action_init
