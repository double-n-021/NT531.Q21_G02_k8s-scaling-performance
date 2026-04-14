FROM python:3.9-slim AS builder 
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim
# PHẢI đặt ENV này ở giai đoạn chạy App
ENV PYTHONUNBUFFERED=1 
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY app.py .

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

# Chạy 2 workers để máy ảo nhẹ hơn và log ổn định hơn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]