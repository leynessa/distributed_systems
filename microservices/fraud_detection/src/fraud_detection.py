
import sys
import os
import grpc
from concurrent import futures
import random

# Add the path to the utils/pb/src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../utils/pb/src')))

# Import the generated gRPC stubs
from utils.pb.src import fraud_pb2, fraud_pb2_grpc

class FraudCheckerServicer(fraud_pb2_grpc.FraudCheckerServicer):
    def CheckFraud(self, request, context):
        is_fraudulent = random.choice([True, False])
        print(is_fraudulent)
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
