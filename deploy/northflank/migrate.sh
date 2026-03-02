#!/usr/bin/env sh
set -eu

DSN="${POSTGRES_DSN_SYNC:-${POSTGRES_DSN:-}}"

if [ -z "${DSN}" ]; then
  echo "POSTGRES_DSN_SYNC or POSTGRES_DSN must be set" >&2
  exit 1
fi

echo "Applying migrations using ${DSN}"

psql "${DSN}" -v ON_ERROR_STOP=1 -f migrations/001_init.sql
psql "${DSN}" -v ON_ERROR_STOP=1 -f migrations/002_seed.sql
psql "${DSN}" -v ON_ERROR_STOP=1 -f migrations/003_admin_guest_hard_delete.sql
psql "${DSN}" -v ON_ERROR_STOP=1 -f migrations/004_tajik_locale_and_service_name.sql

echo "Migrations completed successfully"
