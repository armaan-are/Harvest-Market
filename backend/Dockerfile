FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./backend/

ENV PYTHONPATH=/app
ENV TEAM21_DB_PATH=/app/backend/data/team21_market.db

EXPOSE 8000

CMD ["sh", "-c", "python -m backend.init_db && python -m backend.main"]
