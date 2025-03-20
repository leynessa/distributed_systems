import grpc
from concurrent import futures
import random
import sys
sys.path.append('/app/utils/pb/src')  # Adjust if necessary


from utils.pb.src  import transaction_pb2
from utils.pb.src  import transaction_pb2_grpc

class TransactionVerifierServicer(transaction_pb2_grpc.TransactionVerifierServicer):
    def VerifyTransaction(self, request, context):
        # Simple implementation that randomly verifies the transaction
        # In a real system, this would actually validate the credit card details
        credit_card = request.creditCard
        print(f"Verifying transaction for card ending in {credit_card.number[-4:]}")
        
        # For this example, just randomly approve or decline
        is_valid = random.choice([True, False])
        print(f"Transaction verification result: {is_valid}")
        
        return transaction_pb2.TransactionResponse(isValid=is_valid)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_pb2_grpc.add_TransactionVerifierServicer_to_server(TransactionVerifierServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("Transaction verification service running on port 50052...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()


"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
import re

app = FastAPI()

class CreditCard(BaseModel):
    number: str = Field(..., pattern=r"^\d{16}$")
    expirationDate: str = Field(..., pattern=r"^(0[1-9]|1[0-2])/\d{2}$")
    cvv: str = Field(..., pattern=r"^\d{3}$")

class TransactionRequest(BaseModel):
    creditCard: CreditCard

class TransactionResponse(BaseModel):
    isValid: bool

@app.post("/verify_transaction", response_model=TransactionResponse)  # Change to POST
def verify_transaction(request: TransactionRequest):
    def is_valid_credit_card(creditCard: CreditCard):
        # Check if the card number, expiration date, and CVV are valid
        return (
            bool(re.match(r"^\d{16}$", creditCard.number)) and
            bool(re.match(r"^(0[1-9]|1[0-2])/\d{2}$", creditCard.expirationDate)) and
            bool(re.match(r"^\d{3}$", creditCard.cvv))
        )
    
    print(request)
    # Validate the credit card fields
    is_valid = is_valid_credit_card(request.creditCard)
    
    return TransactionResponse(isValid=is_valid)
"""