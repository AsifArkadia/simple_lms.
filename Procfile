release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && (test -f jwt-signing.pem || python manage.py make_jwt_key) && python manage.py ensure_superuser
web: gunicorn config.wsgi --bind 0.0.0.0:$PORT
