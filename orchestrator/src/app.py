import sys
import os
import grpc
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import threading
import utils.pb.fraud_detection.fraud_detection_pb2 as fraud_pb2
import utils.pb.fraud_detection.fraud_detection_pb2_grpc as fraud_pb2_grpc
import utils.pb.transaction_verification.transaction_verification_pb2 as transaction_pb2
import utils.pb.transaction_verification.transaction_verification_pb2_grpc as transaction_pb2_grpc
import utils.pb.suggestions.suggestions_pb2 as suggestions_pb2
import utils.pb.suggestions.suggestions_pb2_grpc as suggestions_pb2_grpc
import utils.pb.fraud_detection.fraud_detection_pb2 as hello_pb2
import utils.pb.fraud_detection.fraud_detection_pb2_grpc as hello_pb2_grpc

sys.path.append('/app')
logging.basicConfig(level=logging.INFO)

def greet(name='you'):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        request = hello_pb2.HelloRequest(name=name)
        response = stub.SayHello(request)
        
    return response.greeting



# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/




# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

# Function to call Fraud Detection Service
def check_fraud(order_data, results):
    logging.info(f"Checking fraud for order: {order_data['orderId']}")
    try:
        with grpc.insecure_channel('fraud_detection:50051') as channel:
            stub = fraud_pb2_grpc.FraudDetectionStub(channel)
            request = fraud_pb2.FraudRequest(orderId=order_data['orderId'])
            response = stub.CheckFraud(request)
            results['fraud'] = response.is_fraud
        logging.info(f"Fraud check result for {order_data['orderId']}: {response.is_fraud}")
    except Exception as e:
        logging.error(f"Fraud check failed: {str(e)}")
        results['fraud'] = None
        results['errors'] = results.get('errors', []) + [f"Fraud service error: {str(e)}"]

# Function to call Transaction Verification Service
def verify_transaction(order_data, results):
    try:
        with grpc.insecure_channel('transaction_verification:50052') as channel:
            stub = transaction_pb2_grpc.TransactionVerificationStub(channel)
            request = transaction_pb2.TransactionRequest(orderId=order_data['orderId'], totalAmount=order_data['totalAmount'])
            response = stub.VerifyTransaction(request)
            results['transaction_valid'] = response.isValid
    except Exception as e:
        logging.error(f"Transaction verification failed: {str(e)}")
        results['transaction_valid'] = None
        results['errors'] = results.get('errors', []) + [f"Transaction service error: {str(e)}"]

# Function to call Suggestions Service
def get_suggestions(order_data, results):
    try: 
        with grpc.insecure_channel('suggestions:50053') as channel:
            stub = suggestions_pb2_grpc.SuggestionsStub(channel)
            request = suggestions_pb2.SuggestionsRequest(userId=order_data['userId'])
            response = stub.GetSuggestions(request)
            results['suggestedBooks'] = response.suggestions
    except Exception as e:
        logging.error(f"Suggestions service failed: {str(e)}")
        results['suggestedBooks'] = []
        results['errors'] = results.get('errors', []) + [f"Suggestions service error: {str(e)}"]

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
        'userId': request_data.get('userId', 'user123'),
        'items': request_data.get('items', []),
        'totalAmount': request_data.get('totalAmount', 100.0),
    }
    results = {}

    # Process order (gRPC calls in parallel)
    process_order(order_data, results)

    # Determine order status based on results
    order_approved = not results.get('fraud', False) and results.get('transaction_valid', False)
    


   

    # Consolidate results
    if results.get('fraud', False) or not results.get('transaction_valid'):
        order_status = 'Order Rejected'
    else:
        order_status = 'Order Approved'

    # Construct response
    order_status_response = {
        'orderId': order_data['orderId'],
        'status': order_status,
        'suggestedBooks': results.get('suggestedBooks', [])
    }

    if order_approved and 'suggestedBooks' in results:
        suggested_books = []
        for book_title in results['suggestedBooks']:
            suggested_books.append({
                'title': book_title,
                'author': 'Unknown'  # Example since we don't have author data
            })
        order_status_response['suggestedBooks'] = suggested_books
    else:
        order_status_response['suggestedBooks'] = []

    return jsonify(order_status_response)
   
  


if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0', port=5000, debug=True)
