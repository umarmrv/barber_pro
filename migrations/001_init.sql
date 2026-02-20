CREATE TABLE IF NOT EXISTS clients (
  id BIGSERIAL PRIMARY KEY,
  tg_user_id BIGINT NOT NULL UNIQUE,
  phone_e164 VARCHAR(32),
  locale VARCHAR(5) NOT NULL DEFAULT 'ru',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS services (
  id BIGSERIAL PRIMARY KEY,
  name_ru TEXT NOT NULL,
  name_uz TEXT NOT NULL,
  duration_min INTEGER NOT NULL CHECK (duration_min > 0),
  price_minor INTEGER NOT NULL CHECK (price_minor >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS barbers (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_shifts (
  id BIGSERIAL PRIMARY KEY,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE CASCADE,
  weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_local_time TIME NOT NULL,
  end_local_time TIME NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (barber_id, weekday, start_local_time, end_local_time)
);

CREATE TABLE IF NOT EXISTS admin_users (
  id BIGSERIAL PRIMARY KEY,
  tg_user_id BIGINT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bookings (
  id BIGSERIAL PRIMARY KEY,
  client_id BIGINT REFERENCES clients(id) ON DELETE SET NULL,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE RESTRICT,
  service_id BIGINT REFERENCES services(id) ON DELETE SET NULL,
  starts_at_utc TIMESTAMPTZ NOT NULL,
  ends_at_utc TIMESTAMPTZ NOT NULL,
  status VARCHAR(32) NOT NULL,
  note TEXT,
  created_by_admin_id BIGINT REFERENCES admin_users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  cancelled_at_utc TIMESTAMPTZ,
  CHECK (ends_at_utc > starts_at_utc),
  UNIQUE (barber_id, starts_at_utc, status)
);

CREATE TABLE IF NOT EXISTS booking_events (
  id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  event_type VARCHAR(64) NOT NULL,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reminder_jobs (
  id BIGSERIAL PRIMARY KEY,
  booking_id BIGINT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  kind VARCHAR(16) NOT NULL CHECK (kind IN ('24h', '2h')),
  scheduled_at_utc TIMESTAMPTZ NOT NULL,
  sent_at_utc TIMESTAMPTZ,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (booking_id, kind)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_confirmed_slot
  ON bookings (barber_id, starts_at_utc)
  WHERE status = 'confirmed';

CREATE INDEX IF NOT EXISTS idx_bookings_barber_time
  ON bookings (barber_id, starts_at_utc, ends_at_utc);

CREATE INDEX IF NOT EXISTS idx_bookings_client_status_time
  ON bookings (client_id, status, starts_at_utc);

CREATE INDEX IF NOT EXISTS idx_reminder_jobs_due
  ON reminder_jobs (scheduled_at_utc)
  WHERE sent_at_utc IS NULL;
