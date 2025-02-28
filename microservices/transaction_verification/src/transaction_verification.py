from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
import re

app = FastAPI()

class TransactionRequest(BaseModel):
    creditCard: str

class TransactionResponse(BaseModel):
    isValid: bool

@app.get("/verify_transaction", response_model=TransactionResponse)  # Use POST instead of GET
def verify_transaction(request: TransactionRequest):
    def is_valid_credit_card(creditCard):
        # Check if the card number is exactly 16 digits
        return bool(re.match(r"^\d{16}$", creditCard))
    
    print(request)
    # Check if the items list has elements, userId is present, and creditCard is valid
    is_valid = bool(is_valid_credit_card(request.creditCard))
    
    return TransactionResponse(isValid=is_valid)
