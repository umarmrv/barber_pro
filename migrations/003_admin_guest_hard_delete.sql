ALTER TABLE clients
  ALTER COLUMN tg_user_id DROP NOT NULL;

ALTER TABLE clients
  ADD COLUMN IF NOT EXISTS tg_username TEXT,
  ADD COLUMN IF NOT EXISTS tg_first_name TEXT,
  ADD COLUMN IF NOT EXISTS tg_last_name TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_phone_unique_not_null
  ON clients (phone_e164)
  WHERE phone_e164 IS NOT NULL;

ALTER TABLE bookings
  ALTER COLUMN barber_id DROP NOT NULL;

ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS bookings_barber_id_fkey;

ALTER TABLE bookings
  ADD CONSTRAINT bookings_barber_id_fkey
  FOREIGN KEY (barber_id)
  REFERENCES barbers (id)
  ON DELETE SET NULL;

ALTER TABLE reminder_jobs
  DROP CONSTRAINT IF EXISTS reminder_jobs_kind_check;

ALTER TABLE reminder_jobs
  ADD CONSTRAINT reminder_jobs_kind_check
  CHECK (kind IN ('24h', '2h', '30m'));
