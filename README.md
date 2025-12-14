# Transactional System Core

Внутреннее ядро перевода бонусов для сотрудников: кошельки, транзакции, API `/api/transfer`, отложенные уведомления через Celery.

## Требования

- Python 3.11+
- PostgreSQL 13+
- Redis (для брокера Celery)

## Установка

1. Скопируйте переменные окружения: `cp .env.example .env` (при необходимости обновите значения).
2. Установите зависимости и активируйте окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Миграции и начальный кошелек

```bash
python manage.py migrate
```

Миграция `0002_create_admin_wallet` автоматически создаёт технический кошелёк `admin`, который используется для списания комиссии.

## Локальный запуск (без Docker)

В одном терминале:

```bash
python manage.py runserver
```

Во втором терминале:

```bash
celery -A transactional_core worker -l info
```

## API: POST `/api/transfer`

```http
POST /api/transfer
Content-Type: application/json

{
  "source_wallet_id": 1,
  "destination_wallet_id": 2,
  "amount": "1500.00"
}
```

Ответ:

```json
{
  "id": "b9789efd-0b0c-4aab-8461-9a99eb562fe1",
  "source": 1,
  "destination": 2,
  "amount": "1500.00",
  "commission_amount": "150.00",
  "total_debited": "1650.00",
  "created_at": "2024-05-01T12:00:00Z",
  "commission_applied": true
}
```

### Гарантии

- **Race condition**: Списания выполняются в `select_for_update` транзакции и отсортированы по ID, поэтому параллельные запросы одного пользователя не смогут уйти в минус (Double Spending).
- **Комиссия**: Переводы свыше `1000 u.` автоматически начисляют 10% на кошелёк `admin`. Списания, зачисления и комиссия проходят в одной транзакции.

## Уведомления через Celery

После успешного перевода запускается задача `wallets.tasks.send_transfer_notification`. Она:

1. Эмулирует долгий вызов (`time.sleep(5)`).
2. При ошибке автоматически ретраится максимум 3 раза с задержкой 3 секунды.

Это позволяет безопасно интегрироваться с внешними системами уведомлений.

## Запуск через Docker Compose

1. Подготовьте переменные окружения:
   ```bash
   cp .env.example .env
   ```
   Значения Postgres/Redis можно оставить дефолтными — Compose сам проставит `POSTGRES_HOST`, `CELERY_BROKER_URL` и `CELERY_RESULT_BACKEND` внутри контейнеров.
2. Соберите и запустите стек:
   ```bash
   docker compose up --build
   ```
   Поднимаются четыре сервиса: `db` (PostgreSQL 15), `redis`, `web` (Django runserver) и `worker` (Celery). EntryPoint `web` ждёт БД и выполняет миграции, у `worker` миграции отключены (`MIGRATE_ON_START=false`), поэтому коллизий нет.
3. После старта API доступно на `http://127.0.0.1:8000/api/transfer`, а исходный код монтируется внутрь контейнеров (`.:/app`), поэтому правки из IDE сразу попадают в приложение.
4. Полезные команды:
   ```bash
   docker compose exec web python manage.py shell    # открыть Django shell
   docker compose exec web sh -c "pip install requests >/dev/null && python scripts/stress.py"  # стресс-тест
   docker compose logs -f worker                     # логи Celery
   curl -X POST http://127.0.0.1:8000/api/transfer \
     -H "Content-Type: application/json" \
     -d '{"source_wallet_id":2,"destination_wallet_id":3,"amount":"1500.00"}'
   ```
5. Остановка и очистка:
   ```bash
   docker compose down        # остановить контейнеры
   docker compose down -v     # остановить и удалить volume с данными Postgres
   ```

Этот сценарий покрывает все шаги демонстрации: создание кошельков, одиночный перевод с комиссией, запуск параллельного стресс-теста и просмотр уведомлений в Celery.
