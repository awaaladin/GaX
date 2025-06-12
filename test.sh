#!/bin/bash
# Test script for Django Banking API
set -e

export DJANGO_SETTINGS_MODULE=banking.settings
python manage.py test --verbosity=2
