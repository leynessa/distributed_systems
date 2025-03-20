import sys
import os
import grpc
from concurrent import futures
import random

# Add the path to the utils/pb/src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../utils/pb/src')))

# Debug: Print the Python path
print("Python Path:", sys.path)

# Import the generated gRPC stubs
try:
    from utils.pb.src import fraud_detection_pb2, fraud_detection_pb2_grpc
    print("Successfully imported fraud_detection_pb2 and fraud_detection_pb2_grpc")
except ImportError as e:
    print(f"ImportError: {e}")
    print("Ensure that the fraud_detection_pb2.py and fraud_detection_pb2_grpc.py files exist in utils/pb/src/")
    sys.exit(1)

class FraudCheckerServicer(fraud_detection_pb2_grpc.FraudCheckerServicer):
    def CheckFraud(self, request, context):
        # Randomly approve or decline the transaction (for demonstration purposes)
        is_fraudulent = random.choice([True, False])
        print(f"Transaction fraud check result: {is_fraudulent}")
        return fraud_detection_pb2.FraudResponse(isFraudulent=is_fraudulent)

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the FraudChecker service to the server
    fraud_detection_pb2_grpc.add_FraudCheckerServicer_to_server(FraudCheckerServicer(), server)
    
    # Bind the server to port 50051
    server.add_insecure_port('[::]:50051')
    print("gRPC server is running on port 50051...")
    
    # Start the server
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()