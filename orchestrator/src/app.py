import sys
import os
<<<<<<< Updated upstream
=======
from fastapi import FastAPI, Request, HTTPException
import grpc

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import requests
>>>>>>> Stashed changes

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

<<<<<<< Updated upstream
import grpc

def greet(name='you'):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        response = stub.SayHello(fraud_detection.HelloRequest(name=name))
    return response.greeting

# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
from flask import Flask, request
from flask_cors import CORS
import json
=======
# Add paths to gRPC stubs
sys.path.append('utils/pb/fraud_detection')
sys.path.append('/app/utils/pb/transaction_verification')
sys.path.append('/app/utils/pb/suggestions')




#transaction_request = transaction_pb2.TransactionRequest()  # Creating an instance of the generated class

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


# Ensure gRPC stubs are accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../utils/pb/src')))

# Import gRPC stubs
from utils.pb.src import fraud_pb2, fraud_pb2_grpc
from utils.pb.src import transaction_pb2, transaction_pb2_grpc
from utils.pb.src import books_pb2, books_pb2_grpc

def check_fraud_api(order_data, results):
    try:
        with grpc.insecure_channel("fraud_detection:50051") as channel:
            stub = fraud_pb2_grpc.FraudCheckerStub(channel)
            request = fraud_pb2.FraudRequest(orderId=order_data['orderId'])
            response = stub.CheckFraud(request)
            results['fraud'] = response.isFraudulent
    except grpc.RpcError as e:
        results['fraud'] = None
        print(f"Error contacting fraud detection service: {e}")
>>>>>>> Stashed changes

# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

<<<<<<< Updated upstream
# Define a GET endpoint.
@app.route('/', methods=['GET'])
def index():
    """
    Responds with 'Hello, [name]' when a GET request is made to '/' endpoint.
    """
    # Test the fraud-detection gRPC service.
    response = greet(name='orchestrator')
    # Return the response.
    return response

@app.route('/checkout', methods=['POST'])
def checkout():
=======
def verify_transaction_api(order_data, results):
    try:
        # Establish a connection to the gRPC server
        with grpc.insecure_channel('transaction_verification:50052') as channel:
            stub = transaction_pb2_grpc.TransactionVerifierStub(channel)
            
            # Create the TransactionRequest message
            credit_card = transaction_pb2.TransactionRequest.CreditCard(
                number=order_data['creditCard']['number'],
                expirationDate=order_data['creditCard']['expirationDate'],
                cvv=order_data['creditCard']['cvv']
            )
            
            request = transaction_pb2.TransactionRequest(creditCard=credit_card)
            response = stub.VerifyTransaction(request)
            
            results['transaction_valid'] = response.isValid
    except grpc.RpcError as e:
        results['transaction_valid'] = None
        print(f"Error contacting transaction verification service: {e}")


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
    fraud_thread = threading.Thread(target=check_fraud_api, args=(order_data, results))
    transaction_thread = threading.Thread(target=verify_transaction_api, args=(order_data, results))
    suggestions_thread = threading.Thread(target=get_suggestions_api, args=(results,))

    fraud_thread.start()
    transaction_thread.start()
    suggestions_thread.start()

    fraud_thread.join()
    transaction_thread.join()
    suggestions_thread.join()

@app.post("/checkout")
async def checkout(request: Request):
>>>>>>> Stashed changes
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    # Get request object data to json
    request_data = json.loads(request.data)
    # Print request object data
    print("Request Data:", request_data.get('items'))

    # Dummy response following the provided YAML specification for the bookstore
    order_status_response = {
        'orderId': '12345',
        'status': 'Order Approved',
        'suggestedBooks': [
            {'bookId': '123', 'title': 'The Best Book', 'author': 'Author 1'},
            {'bookId': '456', 'title': 'The Second Best Book', 'author': 'Author 2'}
        ]
    }

    return order_status_response

<<<<<<< Updated upstream

if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0')
=======
    # Default to rejecting if any service fails
    is_fraudulent = results.get('fraud', True)  # Default to True if service fails
    is_valid_transaction = results.get('transaction_valid', False)  # Default to False if service fails



    if not is_fraudulent and is_valid_transaction:
        response_json = {
            'status': 'Order Approved',
            'orderId': order_data['orderId'],
            'suggestedBooks': results.get('suggestions', [])
        }
        return response_json
    else:
        error_message = "Order rejected: "
        if is_fraudulent:
            error_message += "Potential fraud detected. "
        if not is_valid_transaction:
            error_message += "Transaction validation failed."
        
        response_json = {
            'status': 'Order Rejected',
            'orderId': order_data['orderId'],
            'error': {'message': error_message.strip()}
        }
        return response_json
>>>>>>> Stashed changes
