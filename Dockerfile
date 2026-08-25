FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8003

CMD ["uvicorn", "apps.main:app", "--host", "0.0.0.0", "--port", "8003"]