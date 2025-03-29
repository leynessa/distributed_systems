import sys
import os
from fastapi import FastAPI, Request, HTTPException

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import requests

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/fraud_detection")
)
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/suggestions")
)
transaction_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/transaction_service")
)
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(1, suggestions_grpc_path)
sys.path.insert(2, transaction_grpc_path)

import books_pb2
import books_pb2_grpc

import fraud_pb2
import fraud_pb2_grpc

import transaction_pb2 as transaction_verification
import transaction_pb2_grpc

# Create a FastAPI app.
app = FastAPI()

# Enable CORS for the app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

import grpc


# class VectorClock:
#     def __init__(self):
#         self.clock = [0, 0, 0]

#     def update(self, clock):
#         self.clock = [max(a, b) for a, b in zip(self.clock, clock)]

#     def to_proto(self,service):


def check_fraud_api(order_data, results):
    channel = grpc.insecure_channel("fraud_detection:50051")
    stub = fraud_pb2_grpc.FraudCheckerStub(channel)
    try:
        request = fraud_pb2.FraudRequest(orderId=order_data["orderId"])
        response = stub.CheckFraud(request)
        results["fraud"] = response.isFraudulent
        
    except grpc.RpcError as e:
        results["fraud"] = None
        print(f"Error contacting fraud detection service: {e}")


def verify_transaction_api(verification_info, results):
    channel = grpc.insecure_channel("transaction_verification:50051")
    stub = transaction_pb2_grpc.TransactionServiceStub(channel)

    # credit_card = transaction_pb2.CreditCard(
    #     number=order_data["creditCard"]["number"],
    #     expirationDate=order_data["creditCard"]["expirationDate"],
    #     cvv=order_data["creditCard"]["cvv"],
    # )
    # request = transaction_pb2.TransactionRequest(creditCard=credit_card)
    print(f"Verification Info: {verification_info}")
    request = transaction_verification.TransactionRequest(
        user=transaction_verification.TransactionUser(
            name=verification_info.get("user", {}).get("name", ""),
            contact=verification_info.get("user", {}).get("contact", ""),
        ),
        creditCard=transaction_verification.CreditCard(
            number=verification_info.get("creditCard", {}).get("number", ""),
            expirationDate=verification_info.get("creditCard", {}).get(
                "expirationDate", ""
            ),
            cvv=verification_info.get("creditCard", {}).get("cvv", ""),
        ),
        items=[
            transaction_verification.TransactionItem(
                name=item.get("name", ""), quantity=item.get("quantity", 0)
            )
            for item in verification_info.get("items", [])
        ],
        billingAddress=transaction_verification.TransactionBillingAddress(
            street=verification_info.get("billingAddress", {}).get("street", ""),
            city=verification_info.get("billingAddress", {}).get("city", ""),
            country=verification_info.get("billingAddress", {}).get("country", ""),
        ),
    )

    try:
        response = stub.VerifyTransaction(request)
        print(f"Transaction Response: {response}")
        results["transaction_valid"] = response.isValid
    except grpc.RpcError as e:
        results["transaction_valid"] = None
        print(f"Error contacting transaction verification service: {e}")


def get_suggestions_api(order_data, results):
    try:
        # Establish a connection to the gRPC server
        with grpc.insecure_channel("suggestions:50053") as channel:
            stub = books_pb2_grpc.BookServiceStub(channel)

            # Create the BookRequest message (you can add parameters if needed)
            request = (
                books_pb2.BookRequest()
            )  # No parameters specified in the proto for this request
            response = stub.GetSuggestions(request)
            print(f"Suggestions: {response}")
            # Process the response
            if response.books:
                results["suggestions"] = [
                    {"title": book.title, "author": book.author}
                    for book in response.books
                ]
            else:
                results["suggestions"] = []

    except grpc.RpcError as e:
        results["suggestions"] = []
        print(f"Error contacting suggestions service: {e.details()}")


import uuid


# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Generate unique order ID
    order_data["orderId"] = str(uuid.uuid4())
    print(f"Generated Order ID: {order_data['orderId']}")

    def check_fraud():
        # order_data["vectorClock"][0] += 1  # Update fraud_thread timestamp before call
        check_fraud_api(order_data, results)  # Pass order_data with vector clock

    def verify_transaction():
        fraud_thread.join()  # Ensure fraud check completes first
        # order_data["vectorClock"][
        #     1
        # ] += 1  # Update transaction_thread timestamp before call
        verify_transaction_api(order_data, results)  # Pass order_data with vector clock

    def get_suggestions():
        transaction_thread.join()  # Ensure transaction check completes first
        # order_data["vectorClock"][
        #     2
        # ] += 1  # Update suggestions_thread timestamp before call
        get_suggestions_api(order_data, results)  # Pass order_data with vector clock

    # Create threads for gRPC calls
    fraud_thread = threading.Thread(target=check_fraud)
    transaction_thread = threading.Thread(target=verify_transaction)
    suggestions_thread = threading.Thread(target=get_suggestions)

    # Start threads
    fraud_thread.start()
    fraud_thread.join()

    transaction_thread.start()
    transaction_thread.join()

    suggestions_thread.start()
    suggestions_thread.join()

    # print(f"Order completed")
    # print(f"Order processing completed. Vector Clock: {order_data['vectorClock']}")


@app.post("/checkout")
async def checkout(request: Request):
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    order_data = {
        "orderId": request_data.get("orderId", "12345"),
        "userId": request_data.get("userId", ""),
        "user": request_data.get("user", {}),
        "items": request_data.get("items", []),
        "totalAmount": request_data.get("totalAmount", 0.0),
        "creditCard": request_data.get("creditCard"),
        "billingAddress": request_data.get("billingAddress", {}),
    }
    results = {}

    # Process order (API calls in parallel)
    process_order(order_data, results)
    print("results:", results)
    if not results.get("fraud", True) and results.get("transaction_valid", False):
        response_json = {
            "status": "Order Approved",
            "orderId": order_data["orderId"],
            "suggestedBooks": results.get("suggestions", []),
        }
        return response_json
    else:
        response_json = {
            "status": "Order Rejected",
            "orderId": order_data["orderId"],
            "suggestedBooks": [],
            "error": {"message": "Fraud detected or transaction invalid"},
        }
        return response_json
