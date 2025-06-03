#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py flush --noinput
python manage.py migrate --run-syncdb
python manage.py loaddata db_data_cleaned.json
