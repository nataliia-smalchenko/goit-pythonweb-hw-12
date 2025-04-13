FROM python:3.12-alpine

ENV APP_HOME=/app
WORKDIR $APP_HOME

# Встановлення додаткових пакетів (gcc, musl-dev, postgresql-dev, python3-dev та netcat для перевірки доступності)
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    netcat-openbsd

COPY requirements.txt $APP_HOME/requirements.txt
RUN pip install -r requirements.txt

COPY . .

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["fastapi", "run", "main.py"]
