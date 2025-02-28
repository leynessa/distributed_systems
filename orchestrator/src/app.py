import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

import grpc

def greet(name='you'):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        response = stub.SayHello(fraud_detection.HelloRequest(name=name))
    return response.greeting

from flask import Flask, request, jsonify

# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
from flask import Flask, request, jsonify 
from flask_cors import CORS
import json

import grpc
import threading
import utils.pb.fraud_detection.fraud_detection_pb2 as fraud_pb2
import utils.pb.fraud_detection.fraud_detection_pb2_grpc as fraud_pb2_grpc
import utils.pb.transaction_verification.transaction_verification_pb2 as transaction_pb2
import utils.pb.transaction_verification.transaction_verification_pb2_grpc as transaction_pb2_grpc
import utils.pb.suggestions.suggestions_pb2 as suggestions_pb2
import utils.pb.suggestions.suggestions_pb2_grpc as suggestions_pb2_grpc


# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

# Function to call Fraud Detection Service
def check_fraud(order_data, results):
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        stub = fraud_pb2_grpc.FraudDetectionStub(channel)
        request = fraud_pb2.FraudRequest(orderId=order_data['orderId'])
        response = stub.CheckFraud(request)
        results['fraud'] = response.isFraudulent

# Function to call Transaction Verification Service
def verify_transaction(order_data, results):
    with grpc.insecure_channel('transaction_verification:50052') as channel:
        stub = transaction_pb2_grpc.TransactionVerificationStub(channel)
        request = transaction_pb2.TransactionRequest(orderId=order_data['orderId'], totalAmount=order_data['totalAmount'])
        response = stub.VerifyTransaction(request)
        results['transaction_valid'] = response.isValid

# Function to call Suggestions Service
def get_suggestions(order_data, results):
    with grpc.insecure_channel('suggestions:50053') as channel:
        stub = suggestions_pb2_grpc.SuggestionsStub(channel)
        request = suggestions_pb2.SuggestionsRequest(userId=order_data['userId'])
        response = stub.GetSuggestions(request)
        results['suggestedBooks'] = [{'bookId': book.bookId, 'title': book.title, 'author': book.author} for book in response.books]

# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Create threads for gRPC calls
    fraud_thread = threading.Thread(target=check_fraud, args=(order_data, results))
    transaction_thread = threading.Thread(target=verify_transaction, args=(order_data, results))
    suggestions_thread = threading.Thread(target=get_suggestions, args=(order_data, results))
    # Start threads
    fraud_thread.start()
    transaction_thread.start()
    suggestions_thread.start()

    # Wait for all threads to finish
    fraud_thread.join()
    transaction_thread.join()
    suggestions_thread.join()


# Define a GET endpoint.
@app.route('/', methods=['GET'])
def index():
    """
    Responds with 'Hello, [name]' when a GET request is made to '/' endpoint.
    """
    # Test the fraud-detection gRPC service.
    response = greet(name='vanessa')
    # Return the response.
    return response

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    # Get request object data to json
    request_data = json.loads(request.data)
    order_data = {
        'orderId': request_data.get('orderId', '12345'),
        'userId': request_data.get('userId', ''),
        'items': request_data.get('items', []),
        'totalAmount': request_data.get('totalAmount', 0.0),
    }
    results = {}

    # Process order (gRPC calls in parallel)
    process_order(order_data, results)

   

    # Consolidate results
    if results.get('fraud') or not results.get('transaction_valid'):
        order_status = 'Order Rejected'
    else:
        order_status = 'Order Approved'

    # Construct response
    order_status_response = {
        'orderId': order_data['orderId'],
        'status': order_status,
        'suggestedBooks': results.get('suggestedBooks', [])
    }

    return jsonify(order_status_response)
   
  


if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0', port=5000, debug=True)
