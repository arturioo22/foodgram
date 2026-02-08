FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn==23.0.0 \
    && apt-get purge -y --auto-remove gcc

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:9000", "foodgram.wsgi:application"]