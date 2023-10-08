#!/bin/sh
echo "Starting server..."
echo "Current directory: $(pwd)"
python -m gunicorn --config scripts/wsgi.py app:server
