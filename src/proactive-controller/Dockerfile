FROM python:3.8-slim

WORKDIR /app

# Cài đặt các thư viện cần thiết
# Lưu ý: Ép phiên bản 0.5.1 cho prometheus-api-client
RUN pip install --no-cache-dir \
    prometheus-api-client==0.5.1 \
    prometheus-client \
    scikit-learn \
    numpy \
    requests

COPY predictive_controller.py .

CMD ["python", "predictive_controller.py"]
