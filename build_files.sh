#!/bin/bash

# Build script for Vercel deployment
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
