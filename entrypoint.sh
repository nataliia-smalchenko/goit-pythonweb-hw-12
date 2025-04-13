#!/bin/sh

# Чекаємо, поки база даних стане доступною
echo "⏳ Чекаю, поки PostgreSQL буде готовий..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "✅ PostgreSQL готовий!"

# Створюємо таблиці (залежно від твоєї реалізації)
# Наприклад, якщо використовуєш Alembic:
alembic upgrade head

# Якщо вручну через SQLAlchemy create_all:
# python create_tables.py

# Запускаємо додаток
exec "$@"
