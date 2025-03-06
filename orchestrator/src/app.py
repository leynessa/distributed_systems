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

def check_fraud_api(order_data, results):
    url = "http://fraud_detection:50051/check_fraud"
    try:
        response = requests.get(url, json={"orderId": order_data['orderId']})
        response.raise_for_status()
        results['fraud'] = response.json()["isFraudulent"]
    except requests.RequestException as e:
        results['fraud'] = None
        print(f"Error contacting fraud detection service: {e}")


def verify_transaction_api(order_data, results):
    print("order_data", order_data)
    url = "http://transaction_verification:50052/verify_transaction"
    try:
        response = requests.post(url, json={"creditCard": order_data['creditCard']})
        response.raise_for_status()
        results['transaction_valid'] = response.json()["isValid"]
    except requests.RequestException as e:
        results['transaction_valid'] = None
        print(f"Error contacting transaction verification service: {e}")



import grpc
from . import books_pb2
from . import books_pb2_grpc

def get_suggestions_api(results):
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


# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Create threads for gRPC calls
    fraud_thread = threading.Thread(target=check_fraud_api, args=(order_data, results))
    suggestions_thread = threading.Thread(target=get_suggestions_api, args=(results,))
    transaction_thread = threading.Thread(target=verify_transaction_api, args=(order_data, results))
    # Start threads
    fraud_thread.start()
    transaction_thread.start()
    suggestions_thread.start()

    # Wait for all threads to finish
    fraud_thread.join()
    transaction_thread.join()
    suggestions_thread.join()

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

    if results.get('fraud', False) and results.get('fraud', False):
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
