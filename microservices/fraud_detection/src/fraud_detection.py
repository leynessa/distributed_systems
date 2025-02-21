from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random

app = FastAPI()

class FraudRequest(BaseModel):
    orderId: str

class FraudResponse(BaseModel):
    isFraudulent: bool

@app.post("/check_fraud", response_model=FraudResponse)
def check_fraud(request: FraudRequest):
    # Random result logic
    is_fraudulent = random.choice([True, False])
    return FraudResponse(isFraudulent=is_fraudulent)
