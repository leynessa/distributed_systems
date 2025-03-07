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
