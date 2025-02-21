import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)

# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
from flask import Flask, request
from flask_cors import CORS
import json

<<<<<<< Updated upstream
=======

import threading
import requests


>>>>>>> Stashed changes
# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

<<<<<<< Updated upstream
=======

def check_fraud_api(order_data, results):
    url = "http://fraud_detection:50051/check_fraud"
    try:
        response = requests.post(url, json={"orderId": order_data['orderId']})
        response.raise_for_status()
        results['fraud'] = response.json()["isFraudulent"]
    except requests.RequestException as e:
        results['fraud'] = None
        print(f"Error contacting fraud detection service: {e}")


def verify_transaction_api(transaction_data, results):
    url = "http://transaction_verification:50052/verify_transaction"
    try:
        response = requests.post(url, json=transaction_data)
        response.raise_for_status()
        results['transaction_valid'] = response.json()["isValid"]
    except requests.RequestException as e:
        results['transaction_valid'] = None
        print(f"Error contacting transaction verification service: {e}")


def get_suggestions_api(preferences, results):
    url = "http://suggestions_service:50053/get_suggestions"
    try:
        response = requests.post(url, json={"preferences": preferences})
        response.raise_for_status()
        results['suggestions'] = response.json()["bookSuggestions"]
    except requests.RequestException as e:
        results['suggestions'] = None
        print(f"Error contacting suggestions service: {e}")


# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Create threads for gRPC calls
    fraud_thread = threading.Thread(target=check_fraud_api, args=(order_data, results))
    transaction_thread = threading.Thread(target=get_suggestions_api, args=(order_data, results))
    suggestions_thread = threading.Thread(target=verify_transaction_api, args=(order_data, results))
    # Start threads
    fraud_thread.start()
    transaction_thread.start()
    suggestions_thread.start()

    # Wait for all threads to finish
    fraud_thread.join()
    transaction_thread.join()
    suggestions_thread.join()


>>>>>>> Stashed changes
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
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    # Get request object data to json
    request_data = json.loads(request.data)
<<<<<<< Updated upstream
=======
    order_data = {
        'orderId': request_data.get('orderId', '12345'),
        'userId': request_data.get('userId', ''),
        'items': request_data.get('items', []),
        'totalAmount': request_data.get('totalAmount', 0.0),
    }
    results = {} 

    # Process order (gRPC calls in parallel)
    process_order(order_data, results)

    # Create threads for gRPC calls
    #fraud_thread = threading.Thread(target=check_fraud, args=(order_data, results))
    #transaction_thread = threading.Thread(target=verify_transaction, args=(order_data, results))
    #suggestions_thread = threading.Thread(target=get_suggestions, args=(order_data, results))

    # Start threads
    #fraud_thread.start()
    #transaction_thread.start()
    #suggestions_thread.start()

    # Wait for all threads to finish
    #fraud_thread.join()
    #transaction_thread.join()
    #suggestions_thread.join()

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
   
>>>>>>> Stashed changes
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


if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0')
