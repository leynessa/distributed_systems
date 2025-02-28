import sys
import os
import grpc
from concurrent import futures
import logging

sys.path.append('/app')
from utils.pb.transaction_verification import transaction_verification_pb2
from utils.pb.transaction_verification import transaction_verification_pb2_grpc

class TransactionVerificationServicer(transaction_verification_pb2_grpc.TransactionVerificationServicer):
    def VerifyTransaction(self, request, context):
        logging.info(f"Verifying transaction for order ID: {request.orderId}, amount: {request.totalAmount}")
        is_valid = request.amount > 0  # Simple check: amount must be > 0
        return transaction_verification_pb2.TransactionResponse(isValid=is_valid)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_verification_pb2_grpc.add_TransactionVerificationServicer_to_server(TransactionVerificationServicer(), server)
    port = "50052"
    server.add_insecure_port("[::]:50052")
    server.start()
    logging.info(f"Transaction Verification Service started. Listening on port {port}.")
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
