#!/bin/bash

# Run database migrations
python manage.py migrate --noinput

# Collect static files (so your CSS/images work)
python manage.py collectstatic --noinput



# Start the Gunicorn web server
gunicorn banking.wsgi:application --bind 0.0.0.0:$PORT

