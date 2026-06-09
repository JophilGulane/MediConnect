web: daphne mediconnect.asgi:application --bind 0.0.0.0 --port $PORT
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
