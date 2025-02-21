from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import random
import requests
import re

app = FastAPI()

class TransactionRequest(BaseModel):
    transactionId: str
    items: list = Field(..., min_items=1)
    userId: str
    creditCard: str

class TransactionResponse(BaseModel):
    isValid: bool

@app.post("/verify_transaction", response_model=TransactionResponse)
def verify_transaction(request: TransactionRequest):
    def is_valid_credit_card(card_number):
        return bool(re.match(r"^\d{16}$", card_number))
    
    is_valid = bool(request.items and request.userId and is_valid_credit_card(request.creditCard))
    return TransactionResponse(isValid=is_valid)

