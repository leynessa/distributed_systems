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
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)

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


import requests
import grpc

from . import fraud_pb2
from . import fraud_pb2_grpc

def check_fraud_api(order_data, results):
    channel = grpc.insecure_channel("fraud_detection:50051")
    stub = fraud_pb2_grpc.FraudCheckerStub(channel)
    try:
        request = fraud_pb2.FraudRequest(orderId=order_data['orderId'])
        response = stub.CheckFraud(request)
        results['fraud'] = response.isFraudulent
    except grpc.RpcError as e:
        results['fraud'] = None
        print(f"Error contacting fraud detection service: {e}")


def verify_transaction_api(order_data, results):
    url = "http://transaction_verification:50052/verify_transaction"
    try:
        response = requests.post(url, json={"creditCard": order_data['creditCard']})
        response.raise_for_status()
        results['transaction_valid'] = response.json()["isValid"]
    except requests.RequestException as e:
        results['transaction_valid'] = None
        print(f"Error contacting transaction verification service: {e}")


from . import books_pb2
from . import books_pb2_grpc

def get_suggestions_api(order_data, results):
    try:
        # Establish a connection to the gRPC server
        with grpc.insecure_channel('suggestions:50053') as channel:
            stub = books_pb2_grpc.BookServiceStub(channel)

            # Create the BookRequest message (you can add parameters if needed)
            request = books_pb2.BookRequest()  # No parameters specified in the proto for this request
            response = stub.GetSuggestions(request)

            # Process the response
            if response.books:
                results['suggestions'] = [{'title': book.title, 'author': book.author} for book in response.books]
            else:
                results['suggestions'] = []

    except grpc.RpcError as e:
        results['suggestions'] = None
        print(f"Error contacting suggestions service: {e.details()}")


import uuid

# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Generate unique order ID
    order_data['orderId'] = str(uuid.uuid4())
    print(f"Generated Order ID: {order_data['orderId']}")
    
    # Initialize vector clock
    order_data['vectorClock'] = [0, 0, 0]  # fraud_thread, transaction_thread, suggestions_thread
    
    def check_fraud():
        order_data['vectorClock'][0] += 1  # Update fraud_thread timestamp before call
        check_fraud_api(order_data, results)  # Pass order_data with vector clock
    
    def verify_transaction():
        fraud_thread.join()  # Ensure fraud check completes first
        order_data['vectorClock'][1] += 1  # Update transaction_thread timestamp before call
        verify_transaction_api(order_data, results)  # Pass order_data with vector clock
    
    def get_suggestions():
        transaction_thread.join()  # Ensure transaction check completes first
        order_data['vectorClock'][2] += 1  # Update suggestions_thread timestamp before call
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
    
    print(f"Order processing completed. Vector Clock: {order_data['vectorClock']}")


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
        'orderId': request_data.get('orderId', '12345'),
        'userId': request_data.get('userId', ''),
        'items': request_data.get('items', []),
        'totalAmount': request_data.get('totalAmount', 0.0),
        'creditCard': request_data.get('creditCard'),
    }
    results = {}

    # Process order (API calls in parallel)
    process_order(order_data, results)

    if not results.get('fraud', True) and results.get('transaction_valid', False):
        response_json = {
            'status': 'Order Approved',
            'orderId': order_data['orderId'],
            'suggestedBooks': results.get('suggestions', [])
        }
        return response_json
    else:
        response_json = {
            'status': 'Order Rejected',
            'orderId': order_data['orderId'],
            'error': {'message': 'Fraud detected or transaction invalid'}
        }
        return response_json
