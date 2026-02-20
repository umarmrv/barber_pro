INSERT INTO services (name_ru, name_uz, duration_min, price_minor)
VALUES
  ('Стрижка', 'Soch olish', 30, 150000),
  ('Стрижка + борода', 'Soch + soqol', 45, 220000),
  ('Бритье', 'Soqol olish', 30, 120000)
ON CONFLICT DO NOTHING;

INSERT INTO barbers (name)
VALUES
  ('Akmal'),
  ('Javlon'),
  ('Sardor')
ON CONFLICT DO NOTHING;

DO $$
DECLARE
  b RECORD;
BEGIN
  FOR b IN SELECT id FROM barbers LOOP
    INSERT INTO work_shifts (barber_id, weekday, start_local_time, end_local_time)
    VALUES
      (b.id, 0, '10:00', '19:00'),
      (b.id, 1, '10:00', '19:00'),
      (b.id, 2, '10:00', '19:00'),
      (b.id, 3, '10:00', '19:00'),
      (b.id, 4, '10:00', '19:00'),
      (b.id, 5, '10:00', '19:00')
    ON CONFLICT DO NOTHING;
  END LOOP;
END $$;
