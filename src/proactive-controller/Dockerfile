FROM python:3.8-slim
WORKDIR /app

# Cài đặt thư viện
RUN pip install --no-cache-dir \
    prometheus-api-client==0.5.1 \
    prometheus-client \
    scikit-learn \
    numpy \
    kubernetes \
    requests \
    grpcio \
    grpcio-tools

# SỬA DÒNG NÀY: Copy tất cả file (bao gồm cả grpc_server.py nếu có)
COPY . . 

CMD ["python", "predictive_controller.py"]
