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

1. Убедитесь, что Docker и Docker Compose установлены.
2. Скопируйте `.env.example` → `.env` (можно оставить значения по умолчанию, Compose перезапишет `POSTGRES_HOST`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`).
3. Соберите и поднимите стек:
   ```bash
   docker compose up --build
   ```
   - сервис `web` запускает Django (`python manage.py runserver 0.0.0.0:8000`);
   - `worker` поднимает Celery;
   - `db` — PostgreSQL 15;
   - `redis` — брокер/хранилище Celery.
   При старте миграции выполняются один раз в контейнере `web` (worker их пропускает через `MIGRATE_ON_START=false`).
4. После старта API доступно на `http://127.0.0.1:8000/api/transfer`. Миграции выполняются автоматически в entrypoint, поэтому дополнительных действий не требуется.

Горячая перезагрузка кода сохраняется за счёт монтирования текущей директории в контейнеры `web` и `worker`. Для остановки нажмите `Ctrl+C` и выполните `docker compose down` (по желанию добавьте `-v`, чтобы удалить volume БД).*** End Patch***}]]
