FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn
EXPOSE 8003

CMD ["python", "./apps/main.py"]