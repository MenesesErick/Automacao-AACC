#!/bin/sh

set -e

echo "Executando migrações do banco de dados..."
python manage.py migrate --noinput

echo "Iniciando Gunicorn..."
exec gunicorn aacc_core.wsgi:application --bind 0.0.0.0:8000
