set -e

while ! mysqladmin ping -h"$DB_HOST" --silent; do
    sleep 1
done

python util_cmd.py create

gunicorn -w 4 'rooms:create_app()' --bind=:8000