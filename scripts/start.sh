#!/bin/sh
python -m gunicorn --config scripts/wsgi.py app:server