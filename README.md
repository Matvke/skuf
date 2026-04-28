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

## Расположение документации

**Engine**
`/engine/docs/openapi.json`

**Proxy**
`/proxy/docs/openapi.json`