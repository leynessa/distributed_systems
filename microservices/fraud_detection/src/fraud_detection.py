import grpc
from concurrent import futures
import sys
import random

utils_path = "/app/utils/pb/fraud_detection"
sys.path.insert(0, utils_path)

import fraud_pb2
import fraud_pb2_grpc

class FraudCheckerServicer(fraud_pb2_grpc.FraudCheckerServicer):
    def CheckFraud(self, request, context):
        is_fraudulent = random.choice([True, False])
        return fraud_pb2.FraudResponse(isFraudulent=is_fraudulent)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    fraud_pb2_grpc.add_FraudCheckerServicer_to_server(FraudCheckerServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server is running on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
