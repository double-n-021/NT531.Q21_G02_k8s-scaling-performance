import grpc
from concurrent import futures
import external_scaler_pb2
import external_scaler_pb2_grpc
import metrics  # Import trực tiếp từ metrics.py

class ExternalScalerServicer(external_scaler_pb2_grpc.ExternalScalerServicer):
    def GetMetricSpec(self, request, context):
        return external_scaler_pb2.GetMetricSpecResponse(
            metricSpecs=[
                external_scaler_pb2.MetricSpec(metricName="future_load", targetSize=2)
            ]
        )

    def GetMetrics(self, request, context):
        # Lấy giá trị mới nhất từ file metrics
        value = int(metrics.LATEST_PREDICTION)
        return external_scaler_pb2.GetMetricsResponse(
            metricValues=[
                external_scaler_pb2.MetricValue(metricName="future_load", metricValue=value)
            ]
        )

    def IsActive(self, request, context):
        return external_scaler_pb2.IsActiveResponse(result=metrics.LATEST_PREDICTION > 0.5)

def start_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    external_scaler_pb2_grpc.add_ExternalScalerServicer_to_server(ExternalScalerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 gRPC server started at :50051", flush=True)
    server.wait_for_termination()
