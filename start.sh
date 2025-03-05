#!/bin/bash

source ./venv/bin/activate

./venv/bin/python --version
./venv/bin/pip install -r requirements.txt
./venv/bin/python app.py -- wpseoscan > ./log/wpseoscan.out 2>&1 &
