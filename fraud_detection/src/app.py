import sys
import os
import grpc
from concurrent import futures
import logging

# Ensure the correct import path for generated protobuf files
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)

import fraud_detection_pb2
import fraud_detection_pb2_grpc

# Fraud detection service implementation
class FraudDetectionServicer(fraud_detection_pb2_grpc.FraudDetectionServicer):
    def CheckFraud(self, request, context):
        # Simple fraud check: consider even order IDs fraudulent
        is_fraud = request.order_id % 2 == 0
        logging.info(f"Processing fraud check for order ID {request.order_id}: Fraud={is_fraud}")
        return fraud_detection_pb2.FraudResponse(is_fraud=is_fraud)

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Register the fraud detection service
    fraud_detection_pb2_grpc.add_FraudDetectionServicer_to_server(FraudDetectionServicer(), server)
    
    # Listen on port 50051
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    
    # Start the server
    server.start()
    logging.info(f"Fraud Detection Service started. Listening on port {port}.")
    
    # Keep the server running
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
