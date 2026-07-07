FROM python:3.12-slim

# Tesseract + basic fonts/libs needed for OCR and PDF rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

WORKDIR /app/backend
RUN mkdir -p uploads logs

ENV TESSERACT_CMD=/usr/bin/tesseract \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=20285

EXPOSE 20285

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "20285", "--workers", "2"]
