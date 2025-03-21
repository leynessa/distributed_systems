import grpc
from concurrent import futures
import re

from . import transaction_pb2
from . import transaction_pb2_grpc

class TransactionService(transaction_pb2_grpc.TransactionServiceServicer):
    def VerifyTransaction(self, request, context):
        def is_valid_credit_card(credit_card):
            return (
                bool(re.match(r"^\d{16}$", credit_card.number)) and
                bool(re.match(r"^(0[1-9]|1[0-2])/\d{2}$", credit_card.expirationDate)) and
                bool(re.match(r"^\d{3}$", credit_card.cvv))
            )

        is_valid = is_valid_credit_card(request.creditCard)
        return transaction_pb2.TransactionResponse(isValid=is_valid)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_pb2_grpc.add_TransactionServiceServicer_to_server(TransactionService(), server)
    server.add_insecure_port("[::]:50051")
    print("gRPC server is running on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
