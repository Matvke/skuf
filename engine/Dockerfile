FROM python:3.14-slim

WORKDIR /app

ENV PYTHONPATH=/app/src

COPY pyproject.toml .

RUN pip install . 

COPY . .

CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]