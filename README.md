# async-payment-process

Микросервис асинхронной обработки платежей. Принимает запрос на оплату, обрабатывает его
через эмулятор платёжного шлюза и уведомляет клиента о результате через webhook.

## Описание

- `POST /api/v1/payments` принимает платёж и сразу отвечает `202 Accepted`. Обработка идёт в фоне.
- Платёж и событие `payments.new` записываются в БД **одной транзакцией** (Outbox pattern).
  Отдельный процесс **outbox relay** публикует события из таблицы `outbox` в RabbitMQ.
- **Consumer** получает событие, эмулирует шлюз (2–5 с, 90% успех / 10% отказ), сохраняет
  статус и отправляет подписанный webhook на `webhook_url` клиента.
- Ошибка обработки (например, недоступен webhook) — **3 повтора** с экспоненциальной
  задержкой 2 / 4 / 8 с, после чего сообщение уходит в **Dead Letter Queue**.
- **Идемпотентность**: заголовок `Idempotency-Key` обязателен. Повтор запроса с тем же ключом
  и телом возвращает исходный платёж; тот же ключ с другим телом — `409 Conflict`.
- Все эндпоинты защищены статическим ключом в заголовке `X-API-Key`.

## Технологии

- Python 3.12, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async, asyncpg), PostgreSQL 17, Alembic
- RabbitMQ 4, FastStream
- httpx (webhook), punq (DI)
- Docker, docker compose, uv
- pytest, Testcontainers, ruff, mypy (strict)

## Архитектура

Путь платежа:

```text
┌──────────┐
│  Клиент  │
└────┬─────┘
     │ POST /api/v1/payments
     │ X-API-Key, Idempotency-Key
     ▼
┌──────────┐    INSERT payment + outbox    ┌──────────────────────┐
│   API    │ ────────────────────────────► │      PostgreSQL      │
└──────────┘      (одна транзакция)        │  payments │  outbox  │
                                           └──────────────────────┘
                                                ▲             ▲
             SELECT ... FOR UPDATE SKIP LOCKED  │             │ UPDATE status,
                           UPDATE published_at  │             │ processed_at
                                        ┌───────┴──────┐      │
                                        │ Outbox relay │      │
                                        └───────┬──────┘      │
                          publish payments.new  │             │
                          (confirm, mandatory)  ▼             │
                                        ┌──────────────┐      │
                                        │   RabbitMQ   │      │
                                        │ payments.new │      │
                                        └───────┬──────┘      │
                            доставка сообщения  │             │
                                                ▼             │
                                        ┌──────────────┐      │
                                        │   Consumer   │──────┘
                                        └───────┬──────┘
                         эмуляция шлюза 2–5 с,  │
                   webhook POST (HMAC-подпись)  │
                                                ▼
                                        ┌──────────────┐
                                        │ webhook_url  │
                                        │   клиента    │
                                        └──────────────┘
```

Повторы и Dead Letter Queue (внутри RabbitMQ):

```text
        ┌───────────────── payments.new ◄─────────────────────┐
        │                                                     │
        ▼                                                     │ TTL истёк
  ┌────────────┐  ошибка, попытка N ≤ 3:  ┌───────────────────┴──┐
  │  Consumer  │ ───────────────────────► │ payments.new.retry.N │
  └─────┬──────┘  publish, ack            │  TTL 2 / 4 / 8 с     │
        │                                 └──────────────────────┘
        │ ошибка после 3-го повтора: reject
        ▼
  ┌──────────────┐        ┌──────────────────┐
  │ payments.dlx │ ─────► │ payments.new.dlq │
  └──────────────┘        └──────────────────┘
```

Процессы (одна кодовая база, отдельные Docker target'ы):

| Сервис | Команда | Назначение |
|---|---|---|
| `migrations` | `alembic upgrade head` | одноразовый, накатывает миграции до старта остальных |
| `api` | `python src/main.py --uvicorn` | HTTP API |
| `outbox-relay` | `python src/main.py --outbox-relay` | публикует события из `outbox` в RabbitMQ |
| `consumer` | `python src/main.py --consumer` | обрабатывает платежи, отправляет webhook |

Слои кода (`src/`):

```
core/         настройки, DI-контейнер, базовая ошибка
domain/       сущности, команды, use case'ы, интерфейсы (Protocol)
infra/        PostgreSQL (модели, репозитории, UoW), RabbitMQ, HTTP, эмулятор шлюза
transport/    FastAPI (api/v1) и обработчики RabbitMQ
entrypoints/  точки входа процессов
```

## Запуск

Нужны Docker и docker compose.

1. Скопировать содержимое `.env.example` в `.env`:

   ```bash
   cp .env.example .env
   ```

2. Поднять всё окружение:

   ```bash
   docker compose up -d --build
   ```

   Поднимаются PostgreSQL, RabbitMQ, затем миграции, затем `api`, `outbox-relay` и `consumer`.

### Ссылки

| Что | Ссылка | Доступ |
|---|---|---|
| Swagger UI | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | кнопка **Authorize** → значение `API_KEY` из `.env` |
| RabbitMQ management | [http://localhost:15672](http://localhost:15672) | `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` из `.env` |

В Swagger можно выполнять запросы прямо из браузера: после **Authorize** заголовок `X-API-Key`
подставляется автоматически, `Idempotency-Key` для `POST` вводится в форме запроса.
В RabbitMQ management на вкладке **Queues** видны очереди `payments.new`, `payments.new.retry.*`
и `payments.new.dlq` — например, сообщения, попавшие в DLQ.

Масштабирование consumer'а:

```bash
docker compose up -d --scale consumer=3
```

### Запуск без Docker (для разработки)

В Docker поднимаются только PostgreSQL и RabbitMQ, процессы приложения запускаются локально.
Хосты `localhost` из `.env` как раз рассчитаны на этот режим.

```bash
cp .env.example .env
uv sync                                    # создаёт .venv и ставит зависимости
source .venv/bin/activate                  # в каждом новом терминале
docker compose up -d async-payment-process-db async-payment-process-rabbitmq

alembic upgrade head

python src/main.py --uvicorn               # API (в отдельном терминале)
python src/main.py --outbox-relay          # outbox relay (в отдельном терминале)
python src/main.py --consumer              # consumer (в отдельном терминале)
```

Если контейнеры `api`, `outbox-relay`, `consumer` из полного запуска ещё работают, их нужно
остановить (`docker compose stop api outbox-relay consumer`), иначе порт 8000 будет занят,
а события будут разбирать два consumer'а.

### Пример запросов

```bash
export API_KEY=$(grep '^API_KEY=' .env | cut -d= -f2-)

curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: 6f1c2a9e-0d3b-4c1e-9a77-2b5f1e8c4d10" \
  -H "Content-Type: application/json" \
  -d '{"amount": "150.00", "currency": "RUB", "description": "Заказ #42",
       "metadata": {"order_id": 42}, "webhook_url": "https://example.com/webhook"}'

curl http://localhost:8000/api/v1/payments/<payment_id> -H "X-API-Key: $API_KEY"
```

Все ответы имеют формат `{"data": {...}, "meta": {}, "errors": [...]}`.

### Коды ошибок

Ошибки возвращаются в `errors` списком элементов `{"code", "message", "details"}`.

| HTTP | `code` | Когда |
|---|---|---|
| 401 | `invalid-api-key` | нет заголовка `X-API-Key` или ключ неверный |
| 404 | `payment-not-found` | платёж с таким `payment_id` не найден |
| 409 | `idempotency-key-conflict` | `Idempotency-Key` уже использован с другим телом запроса |
| 422 | `validation-error` | невалидное тело, заголовок или параметр пути; по одному элементу на каждое поле, путь к полю в `details.loc` |
| 422 | `invalid-payment-amount` | сумма не прошла доменную проверку (`amount > 0`) |
| 500 | `internal-error` | непредвиденная ошибка сервера; детали пишутся в лог и наружу не отдаются |

### Webhook

После обработки платежа consumer отправляет `POST` на `webhook_url`.

Тело запроса:

```json
{
  "payment_id": "d458836d-3ade-4253-887b-197376f12562",
  "status": "succeeded",
  "amount": "150.00",
  "currency": "RUB",
  "processed_at": "2026-10-27T17:47:35.120000+00:00"
}
```

`status` — `succeeded` или `failed`.

Заголовки:

| Заголовок | Значение |
|---|---|
| `X-Webhook-Timestamp` | Unix-время отправки, в секундах |
| `X-Webhook-Signature` | `sha256=<hex>` — HMAC-SHA256 от строки `"{timestamp}.{тело запроса}"` с ключом `WEBHOOK_SECRET` |
| `X-Idempotency-Key` | `payment_id`; доставка «как минимум один раз», повторный webhook по тому же платежу нужно игнорировать |

Ответ `2xx` считается успешной доставкой. Любой другой ответ, таймаут (`WEBHOOK_TIMEOUT`) или
сетевая ошибка — повтор через 2 / 4 / 8 с, затем сообщение уходит в DLQ.

Проверка подписи на стороне получателя:

```python
import hashlib
import hmac
import time


def verify_webhook(body: bytes, timestamp: str, signature: str, secret: str) -> bool:
    if abs(time.time() - int(timestamp)) > 300:  # защита от повторной отправки старого запроса
        return False
    expected = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")
```

Подпись считается от **сырых байтов** тела запроса — их нужно брать до разбора JSON.

## Тесты и проверки

```bash
uv sync                             # зависимости, включая dev
source .venv/bin/activate

pytest tests/unit                   # unit-тесты, без внешних зависимостей
pytest tests/integration            # интеграционные (нужен Docker: Testcontainers поднимает PostgreSQL)
pytest                              # все тесты

ruff check src tests                # линтер
ruff format --check src tests       # проверка форматирования
mypy                                # проверка типов (strict)
```
