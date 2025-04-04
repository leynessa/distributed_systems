import sys
import os
from fastapi import FastAPI, Request, HTTPException

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import requests
import uuid

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
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/order_queue")
)

sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(1, suggestions_grpc_path)
sys.path.insert(2, transaction_grpc_path)
sys.path.insert(3, order_queue_grpc_path)

import books_pb2
import books_pb2_grpc

import fraud_pb2
import fraud_pb2_grpc

import transaction_pb2 as transaction_verification
import transaction_pb2_grpc

import order_queue_pb2
import order_queue_pb2_grpc

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


# utils/vector_clock.py
class VectorClock:
    def __init__(self, initial=None):
        self.clock = initial if initial is not None else {}

    def increment(self, service_name):
        self.clock[service_name] = self.clock.get(service_name, 0) + 1

    def merge(self, other_clock):
        for service, time in other_clock.items():
            self.clock[service] = max(self.clock.get(service, 0), time)

    def to_proto(self, proto_class):
        return proto_class(clock=self.clock)

    @staticmethod
    def from_proto(proto_clock):
        return VectorClock(dict(proto_clock.clock))

def check_fraud_api(order_data, results, vc):
    channel = grpc.insecure_channel("fraud_detection:50051")
    stub = fraud_pb2_grpc.FraudCheckerStub(channel)
    try:
        vc.increment("orchestrator")   

        request = fraud_pb2.FraudRequest(
            orderId=order_data["orderId"],
            vectorClock=vc.to_proto(fraud_pb2.VectorClock)
        )

        response = stub.CheckFraud(request)
        results["fraud_detected"] = response.isFraudulent
        print("true fraud result: ", response.isFraudulent)

        # merge clock з відповіді
        updated_clock = VectorClock.from_proto(response.vectorClock)
        vc.merge(updated_clock.clock)

    except grpc.RpcError as e:
        results["fraud_detected"] = None
        print(f"Error contacting fraud detection service: {e}")



def verify_transaction_api(order_data, results, vc):
    channel = grpc.insecure_channel("transaction_verification:50052")
    stub = transaction_pb2_grpc.TransactionServiceStub(channel)

    print(f"Verification Info: {order_data}")
    request = transaction_verification.TransactionRequest(
        orderId=order_data["orderId"],
        user=transaction_verification.TransactionUser(
            name=order_data.get("user", {}).get("name", ""),
            contact=order_data.get("user", {}).get("contact", ""),
        ),
        creditCard=transaction_verification.CreditCard(
            number=order_data.get("creditCard", {}).get("number", ""),
            expirationDate=order_data.get("creditCard", {}).get("expirationDate", ""),
            cvv=order_data.get("creditCard", {}).get("cvv", ""),
        ),
        items=[
            transaction_verification.TransactionItem(
                name=item.get("name", ""), quantity=item.get("quantity", 0)
            )
            for item in order_data.get("items", [])
        ],
        billingAddress=transaction_verification.TransactionBillingAddress(
            street=order_data.get("billingAddress", {}).get("street", ""),
            city=order_data.get("billingAddress", {}).get("city", ""),
            country=order_data.get("billingAddress", {}).get("country", ""),
        ),
        vectorClock=vc.to_proto(transaction_verification.VectorClock)
    )

    try:
        response = stub.VerifyTransaction(request)
        print(f"Transaction Response: {response.isValid}")
        results["transaction_valid"] = response.isValid

        if hasattr(response, "vectorClock"):
            updated_clock = VectorClock.from_proto(response.vectorClock)
            vc.merge(updated_clock.clock)

    except grpc.RpcError as e:
        results["transaction_valid"] = None
        print(f"Error contacting transaction verification service: {e}")



def get_suggestions_api(order_data, results, vc):
    try:
        with grpc.insecure_channel("suggestions:50053") as channel:
            stub = books_pb2_grpc.BookServiceStub(channel)

            
            vc.increment("orchestrator")

            request = books_pb2.BookRequest(
                orderId=order_data["orderId"],  
                vectorClock=vc.to_proto(books_pb2.VectorClock)
            )


            response = stub.GetSuggestions(request)

            
            response_clock = VectorClock.from_proto(response.vectorClock)
            vc.merge(response_clock.clock)

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

def enqueue_order_api(order_data, results, vc):
    try:
        with grpc.insecure_channel("order_queue:50054") as channel:
            stub = order_queue_pb2_grpc.OrderQueueServiceStub(channel)
            
            # Build the order object from order_data
            order = order_queue_pb2.Order(
                orderId=order_data["orderId"],
                userId=order_data.get("userId", ""),
                user=order_queue_pb2.UserInfo(
                    name=order_data.get("user", {}).get("name", ""),
                    contact=order_data.get("user", {}).get("contact", "")
                ),
                items=[
                    order_queue_pb2.OrderItem(
                        name=item.get("name", ""),
                        quantity=item.get("quantity", 0)
                    ) for item in order_data.get("items", [])
                ],
                billingAddress=order_queue_pb2.BillingAddress(
                    street=order_data.get("billingAddress", {}).get("street", ""),
                    city=order_data.get("billingAddress", {}).get("city", ""),
                    state=order_data.get("billingAddress", {}).get("state", ""),
                    zip=order_data.get("billingAddress", {}).get("zip", ""),
                    country=order_data.get("billingAddress", {}).get("country", "")
                ),
                shippingMethod=order_data.get("shippingMethod", "Standard"),
                giftWrapping=order_data.get("giftWrapping", False)
            )
            
            request = order_queue_pb2.EnqueueRequest(
                order=order,
                vectorClock=vc.to_proto(order_queue_pb2.VectorClock)
            )
            
            response = stub.Enqueue(request)
            results["enqueued"] = response.success
            results["queue_position"] = response.queuePosition
            
            # Update vector clock
            if hasattr(response, "vectorClock"):
                updated_clock = VectorClock.from_proto(response.vectorClock)
                vc.merge(updated_clock.clock)
            
            print(f"Order enqueued: {response.success}, Position: {response.queuePosition}")
    
    except grpc.RpcError as e:
        results["enqueued"] = False
        print(f"Error contacting order queue service: {e.details()}")



# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    order_data["orderId"] = str(uuid.uuid4())
    print(f"Generated Order ID: {order_data['orderId']}")

    # Create vector clock
    vc = VectorClock()

    def check_fraud():
        check_fraud_api(order_data, results, vc)

    def verify_transaction():
        fraud_thread.join()
        vc.increment("orchestrator")
        verify_transaction_api(order_data, results, vc)

    def get_suggestions():
        transaction_thread.join()
        vc.increment("orchestrator")
        get_suggestions_api(order_data, results, vc)

    def enqueue_order():
        suggestions_thread.join()
        vc.increment("orchestrator")
        
        # Only enqueue if order is valid (no fraud detected and transaction is valid)
        if not results.get("fraud_detected", False) and results.get("transaction_valid", False):
            enqueue_order_api(order_data, results, vc)
        else:
            results["enqueued"] = False
            print("Order not enqueued: fraud detected or transaction invalid")


    # Start threads
    fraud_thread = threading.Thread(target=check_fraud)
    transaction_thread = threading.Thread(target=verify_transaction)
    suggestions_thread = threading.Thread(target=get_suggestions)
    enqueue_thread = threading.Thread(target=enqueue_order)

    fraud_thread.start()
    fraud_thread.join()

    transaction_thread.start()
    transaction_thread.join()

    suggestions_thread.start()
    suggestions_thread.join()
    
    enqueue_thread.start()
    enqueue_thread.join()

   


    print(f"Final vector clock: {vc.clock}")


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
        "shippingMethod": request_data.get("shippingMethod", "Standard"),
        "giftWrapping": request_data.get("giftWrapping", False),
        "userComment": request_data.get("userComment", "")
    }
    results = {}

    # Process order (API calls in parallel)
    process_order(order_data, results)
    print("results:", results)

    if not results.get("fraud_detected", False) and results.get("transaction_valid", True):
        response_json = {
            "status": "Order Approved",
            "orderId": order_data["orderId"],
            "suggestedBooks": results.get("suggestions", []),
        }
        # Add queue information if enqueued
        if results.get("enqueued", False):
            response_json["queueStatus"] = {
                "enqueued": True,
                "position": results.get("queue_position", 0)
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
