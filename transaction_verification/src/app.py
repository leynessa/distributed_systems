import grpc
from concurrent import futures
import logging
import transaction_verification_pb2
import transaction_verification_pb2_grpc

class TransactionVerificationServicer(transaction_verification_pb2_grpc.TransactionVerificationServicer):
    def VerifyTransaction(self, request, context):
        is_valid = request.amount > 0  # Simple check: amount must be > 0
        return transaction_verification_pb2.TransactionResponse(is_valid=is_valid)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_verification_pb2_grpc.add_TransactionVerificationServicer_to_server(TransactionVerificationServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
