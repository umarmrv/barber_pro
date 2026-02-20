# Barber Bot: Пошаговая документация и бизнес-логика (RU)

## 1. Что уже реализовано

1. Telegram-бот для записи в барбершоп (RU/UZ).
2. Клиентский поток записи: `Услуга -> Мастер -> Доступные даты -> Доступные слоты -> Подтверждение`.
3. Пользователь видит только реально доступные даты/слоты.
4. Telegram админ-панель (кнопки + FSM):
- CRUD мастеров (создание, переименование, архив/восстановление).
- CRUD услуг (RU/UZ название, длительность, цена, архив/восстановление).
- Смены мастеров: добавление, удаление.
- Массовое редактирование недельного графика мастера.
5. Старые `/admin_*` команды сохранены как fallback.
6. API webhook + idempotency + security checks.
7. Health/readiness endpoints.
8. Scheduler напоминаний `24h` и `2h`.

## 2. Архитектура

1. `api` (FastAPI):
- принимает Telegram updates через webhook;
- health/readiness;
- operational endpoints для webhook.
2. `bot` (aiogram service): вспомогательный runtime сервис.
3. `scheduler`: отправка напоминаний.
4. `postgres`: бизнес-данные.
5. `redis`: FSM, idempotency, drafts.
6. `nginx`: проксирование внешнего трафика к `api`.

## 3. Ключевые файлы

1. Админ-логика: `src/barber_bot/bot/handlers/admin.py`
2. Запись пользователя: `src/barber_bot/bot/handlers/booking.py`
3. Клавиатуры: `src/barber_bot/bot/keyboards.py`
4. FSM состояния: `src/barber_bot/bot/states.py`
5. Репозиторий и CRUD: `src/barber_bot/db/repositories.py`
6. Локализация RU/UZ: `src/barber_bot/i18n.py`
7. API: `src/barber_bot/api/app.py`
8. Compose: `deploy/docker-compose.yml`

## 4. Пошаговый запуск локально (VS Code)

1. Откройте проект в VS Code:
```bash
cd '/Users/shohjahonmurodov/Desktop/barber_pro '
```

2. Подготовьте `.env`:
```bash
cp -n .env.example .env
```

3. Заполните обязательные переменные в `.env`:
```env
BOT_TOKEN=ваш_токен_бота
WEBHOOK_SECRET=сильный_секрет_для_telegram_header
WEBHOOK_URL=https://ваш-домен/telegram/webhook
ADMIN_API_SECRET=сильный_секрет_для_admin_api
POSTGRES_DSN=postgresql+asyncpg://barber:barber@postgres:5432/barber
REDIS_DSN=redis://redis:6379/0
SALON_TIMEZONE=Asia/Tashkent
SKIP_BOT_API_CALLS=false
```

4. Поднимите стек:
```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

5. Проверьте контейнеры:
```bash
docker compose -f deploy/docker-compose.yml ps
```
Ожидание: `postgres` и `redis` healthy, `api` healthy, `nginx` up.

6. Проверьте health/readiness:
```bash
curl -i http://localhost/healthz
curl -i http://localhost/readyz
```
Ожидание:
- `{"status":"ok"}`
- `{"status":"ready"}`

7. Проверьте operational API webhook:
```bash
curl -s -H 'X-Admin-Api-Secret: <ADMIN_API_SECRET>' http://localhost/telegram/webhook_info
curl -s -X POST -H 'X-Admin-Api-Secret: <ADMIN_API_SECRET>' 'http://localhost/telegram/webhook_sync?drop_pending_updates=false'
```

8. Проверка webhook security:
```bash
curl -i -X POST http://localhost/telegram/webhook -H 'Content-Type: application/json' -d '{"update_id":1}'
```
Ожидание: `403` (без правильного `X-Telegram-Bot-Api-Secret-Token`).

9. Проверка webhook idempotency:
- отправьте одинаковый `update_id` дважды с правильным заголовком;
- 1-й запрос: `{"ok":true}`;
- 2-й запрос: `{"ok":true,"duplicate":true}`.

10. Запуск тестов:
```bash
.venv/bin/python -m pytest -q
```

## 5. Пошаговая работа с админ-панелью

1. Убедитесь, что ваш Telegram user id добавлен в `ADMIN_IDS`.
2. В боте отправьте `/admin`.
3. Откроется меню:
- Мастера
- Услуги
- Записи сегодня

### 5.1 Мастера

1. Нажмите `Мастера`.
2. `Добавить` -> введите имя.
3. Откройте карточку мастера:
- `Переименовать`
- `Смены` (точечное управление)
- `Недельный график` (массовая замена)
- `Архивировать` / `Восстановить`

### 5.2 Недельный график (массовое управление)

1. В карточке мастера нажмите `Недельный график`.
2. Отправьте 7 строк (дни `1..7`), формат:
```text
1 10:00-14:00,15:00-19:00
2 10:00-18:00
3 off
4 10:00-18:00
5 10:00-18:00
6 off
7 off
```
3. Это полностью заменит текущие смены мастера.

Правила:
- каждый день `1..7` должен быть указан ровно 1 раз;
- интервалы в пределах дня не должны пересекаться;
- для выходного используйте `off`.

### 5.3 Услуги

1. Нажмите `Услуги`.
2. `Добавить` и пройдите шаги:
- название RU;
- название UZ;
- длительность (мин);
- цена (`price_minor`).
3. В карточке услуги доступно:
- `Редактировать` (все поля);
- `Архивировать` / `Восстановить`.

## 6. Бизнес-логика (ядро системы)

### 6.1 Доменные сущности

1. `Client`: Telegram user, phone, locale.
2. `Service`: RU/UZ names, duration, price, `is_active`.
3. `Barber`: name, `is_active`.
4. `WorkShift`: интервалы работы мастера по weekday.
5. `Booking`: start/end UTC, status (`confirmed/cancelled/blocked`).
6. `ReminderJob`: задания напоминаний `24h/2h`.

### 6.2 Правила бронирования

1. Окно записи: от `now + BOOKING_MIN_LEAD_HOURS` до `now + BOOKING_MAX_DAYS`.
2. Время хранится в UTC, пользователю показывается в `SALON_TIMEZONE`.
3. Слоты генерируются из:
- рабочих смен мастера;
- длительности услуги;
- занятых интервалов (`confirmed` и `blocked`).
4. В UI показываются только дни, где есть хотя бы 1 свободный слот.
5. На подтверждении используется защита от гонок (конкурентных подтверждений):
- проверка пересечений в транзакции;
- при конфликте бронь не создается;
- пользователю показываются пересчитанные доступные даты.

### 6.3 Отмена и ограничения

1. Клиент может отменить только свою `confirmed` запись.
2. Отмена разрешена, если до начала >= `CANCEL_MIN_LEAD_HOURS`.
3. Если меньше порога, приходит отказ `cancel_too_late`.

### 6.4 Soft delete

1. Мастера и услуги не удаляются физически.
2. Архив/восстановление через `is_active=false/true`.
3. Архивные сущности не участвуют в пользовательском потоке записи.
4. История бронирований сохраняется.

### 6.5 Смены и расписание

1. Смена валидна, если `start < end`.
2. Пересечения смен внутри одного дня запрещены.
3. При недельном bulk update старый график заменяется новым атомарно.

### 6.6 Напоминания

1. После успешного `confirmed` создаются `ReminderJob` на `24h` и `2h`.
2. Scheduler выбирает due jobs, отправляет сообщение и отмечает `sent_at`.
3. Дубли исключаются (уникальность по `booking_id + kind`).

### 6.7 Безопасность

1. `POST /telegram/webhook` принимает update только с корректным `X-Telegram-Bot-Api-Secret-Token`.
2. Operational endpoints требуют `X-Admin-Api-Secret`.
3. Idempotency по `update_id` через Redis.

## 7. API контракты

1. `GET /healthz` -> `{"status":"ok"}`
2. `GET /readyz` -> `{"status":"ready"}` или `503`
3. `POST /telegram/webhook` -> `{"ok":true}` / `{"ok":true,"duplicate":true}` / `403`
4. `GET /telegram/webhook_info` (admin secret)
5. `POST /telegram/webhook_sync` (admin secret)
6. `POST /telegram/webhook_delete` (admin secret)

## 8. Типовые инциденты и быстрые проверки

1. `readyz=503`: проверьте `postgres/redis` health в compose.
2. Бот не получает update: проверьте `WEBHOOK_URL`, `webhook_info`, nginx route.
3. `403 webhook`: проверьте `WEBHOOK_SECRET` и заголовок Telegram.
4. Админ API `403`: проверьте `ADMIN_API_SECRET` и `X-Admin-Api-Secret`.
5. Не видно слотов: проверьте активность мастера/услуги, смены и booking window.

## 9. Рекомендованный регламент эксплуатации

1. Перед релизом: `pytest` + smoke `/healthz` `/readyz` `/telegram/webhook_info`.
2. После релиза: проверить `/admin` сценарии CRUD и одну тестовую запись.
3. Ежедневно: мониторить логи `api`, `scheduler`, `bot`.
4. Еженедельно: тест восстановления из backup Postgres.

