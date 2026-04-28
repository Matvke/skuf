FROM golang:1.25-alpine AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY cmd ./cmd
COPY configs ./configs
COPY internal ./internal

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/proxy ./cmd/app

FROM alpine:latest

WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder /out/proxy /app/proxy
COPY --from=builder /src/configs /app/configs

RUN chown -R app:app /app

USER app

EXPOSE 8080

CMD ["./proxy"]
