FROM python:3.12.3-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8004

CMD ["sh", "-c", "daphne -b 0.0.0.0 -p ${PORT:-8004} notification_service.asgi:application"]
