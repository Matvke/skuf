# skuf
С.К.У.Ф — Слой Контроля Утечек и Фильтрации текста. Проект разработанный в рамках проектного практикума ИРИТ-РТФ весна 2026.

## Запуск
`docker-compose up -d`


## Пример конфига для Engine
```
name: default
extractors: [passport, inn, phone]
placeholder: "[СКРЫТО]"
remove_overlaps: true
```

## Пример конфига для Proxy
```
port: 8080
engine_url: http://engine:8000
reload_debounce_ms: 500
targets:
    - name: openai-chat
      match:
        host: localhost:8080
        path: /static
        methods:
            - POST
            - GET
      upstream:
        scheme: http
        host: httpbin.org:443
        path: /
      extract:
        json_paths:
            - data.chat.messages[*].parts[*].text
    - name: anthropic-messages
      match:
        host: api.anthropic.com
        path: /v1/messages
        methods:
            - POST
      upstream:
        scheme: https
        host: api.anthropic.com
        path: /v1/messages
      extract:
        json_paths:
            - messages[*].content
```

## Как пользоваться Proxy

Proxy — HTTP-сервис, который принимает входящие запросы, по конфигу выбирает `target`, извлекает из JSON тела значения по `json_paths`, отправляет их в Engine на анонимизацию и затем форвардит запрос в `upstream` уже с заменёнными значениями.

### Запуск

**Docker Compose**
- `docker-compose up -d`

**Локально (Go)**
- Конфиг по умолчанию: `proxy/configs/config.yaml`
- Запуск из корня репозитория: `go run ./proxy/cmd/app`

Proxy слушает порт из конфига (`port`).

### Быстрый старт: анонимизация запросов к LLM через reverse-proxy

Пример для OpenAI Responses API (клиент шлёт запросы в Proxy, Proxy форвардит в `api.openai.com`):
```yaml
targets:
  - name: openai-responses
    match:
      host: localhost:8080
      path: /v1/responses
      methods: [POST]
    upstream:
      scheme: https
      host: api.openai.com
      path: /v1/responses
    extract:
      json_paths:
        - input
        - instructions
```

Аналогично для Anthropic Messages API:
```yaml
targets:
  - name: anthropic-messages
    match:
      host: localhost:8080
      path: /v1/messages
      methods: [POST]
    upstream:
      scheme: https
      host: api.anthropic.com
      path: /v1/messages
    extract:
      json_paths:
        - messages[*].content
```

### Базовые эндпоинты Proxy

- `GET /api/v1/health` — healthcheck (`ok`)
- `GET /api/v1/debug/config` — текущий скомпилированный конфиг (JSON)
- `POST /api/v1/config` — обновить конфиг, принимает JSON `RawConfig` (структура совпадает с YAML)

### Конфиг и перехват

Proxy **не перехватывает трафик “прозрачно” сам по себе** — его нужно сделать точкой входа для запросов:

1) **Режим reverse-proxy (рекомендуется для разработки/интеграций)**
- Приложение отправляет запросы **в Proxy**, а Proxy уже ходит в upstream.
- В конфиге `match.host` обычно будет равен хосту Proxy (например `localhost:8080`), а `upstream.host` — реальному сервису.

2) **Режим системного HTTP proxy (через настройки ОС/переменные окружения)**
- Приложения, которые поддерживают HTTP proxy, будут слать запросы через Proxy.
- В конфиге `match.host` должен совпадать с реальным `Host` запроса (например `httpbin.org`).

Важно: Proxy анализирует и модифицирует **JSON** тело запроса. Если тело не JSON — запрос будет отклонён с ошибкой парсинга.
Также учти, что `match.path` — это **строгое** совпадение пути (не prefix).

Пример `target` для режима системного HTTP proxy:
```yaml
targets:
  - name: httpbin-anything
    match:
      host: httpbin.org
      path: /anything
      methods: [POST]
    upstream:
      scheme: http
      host: httpbin.org
      path: /anything
    extract:
      json_paths:
        - json.message
```

### Как указать прокси в Linux, чтобы запросы шли через Proxy

#### Временно (только для текущего терминала)

Укажи HTTP proxy на локальный Proxy:
- `export http_proxy=http://127.0.0.1:8080`
- `export HTTP_PROXY=http://127.0.0.1:8080`
- (опционально) `export no_proxy=localhost,127.0.0.1`

Проверка (пример):  
`curl -x http://127.0.0.1:8080 -H 'Content-Type: application/json' -d '{"message":"hello"}' http://httpbin.org/anything`

#### Системные настройки (GNOME)

Settings → Network → Proxy → Manual:
- HTTP Proxy: `127.0.0.1`
- Port: `8080`

Альтернатива через `gsettings`:
- `gsettings set org.gnome.system.proxy mode 'manual'`
- `gsettings set org.gnome.system.proxy.http host '127.0.0.1'`
- `gsettings set org.gnome.system.proxy.http port 8080`

#### Системно для всех процессов (через /etc/environment)

Добавь строки:
```
http_proxy=http://127.0.0.1:8080
HTTP_PROXY=http://127.0.0.1:8080
```
и перезайди в систему.

### Ограничения

- HTTPS-трафик через системный прокси обычно требует метода `CONNECT` и/или MITM для расшифровки. Текущая реализация Proxy работает на уровне HTTP-запросов и модифицирует JSON тела, поэтому “прозрачно” анонимизировать HTTPS без дополнительной TLS-терминации не получится.

## Расположение документации

**Engine**
`/engine/docs/openapi.json`

**Proxy**
`/proxy/docs/openapi.json`
