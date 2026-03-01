ALTER TABLE services
  ADD COLUMN IF NOT EXISTS name_tj TEXT;

UPDATE services
SET name_tj = name_ru
WHERE name_tj IS NULL;

ALTER TABLE services
  ALTER COLUMN name_tj SET NOT NULL;
