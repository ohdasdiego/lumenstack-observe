#!/bin/bash
gunicorn --workers 2 --bind 127.0.0.1:5009 app:app
