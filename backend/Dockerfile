FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    libfreetype6-dev libpng-dev \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir matplotlib==3.9.0 pytesseract==0.3.13

COPY . .
EXPOSE 8000
# PORT lo define la plataforma (Railway/Render); local usa 8000
ENV PORT=8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
