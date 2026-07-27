#!/bin/sh
set -e

echo "Warte auf die Datenbank..."
while ! python -c "import socket; socket.create_connection(('${DB_HOST}', ${DB_PORT}), 2)" 2>/dev/null; do
  sleep 1
done
echo "Datenbank ist erreichbar."

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
