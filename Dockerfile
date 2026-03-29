FROM python:3.11-slim

WORKDIR /app

RUN pip install playwright \
 && playwright install --with-deps chromium

COPY . .

CMD ["python", "app.py"]
