#!/usr/bin/env bash

DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $DIR
source venv/bin/activate

uwsm app -a fabric_shell -- python main.py
