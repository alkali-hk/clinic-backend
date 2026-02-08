web: python manage.py migrate && python manage.py collectstatic --noinput && python init_production_data.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
