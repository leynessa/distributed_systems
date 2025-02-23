import sys
import os
from fastapi import FastAPI, Request
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
    url = "http://fraud_detection:50051/check_fraud"  # Заміна localhost на ім'я сервісу
    try:
        response = requests.get(url, json={"orderId": order_data['orderId']})
        response.raise_for_status()
        results['fraud'] = response.json()["isFraudulent"]
    except requests.RequestException as e:
        results['fraud'] = None
        print(f"Error contacting fraud detection service: {e}")


def verify_transaction_api(order_data, results):
    print("order_data", order_data)  # додайте це для дебагу
    #print("results", results)  # додайте це для дебагу
    url = "http://transaction_verification:50052/verify_transaction"  # Заміна localhost на ім'я сервісу
    try:
        response = requests.get(url, json={"cardNumber": order_data['cardNumber']})
        response.raise_for_status()
        results['transaction_valid'] = response.json()["isValid"]
    except requests.RequestException as e:
        results['transaction_valid'] = None
        print(f"Error contacting transaction verification service: {e}")


def get_suggestions_api(results):
    url = "http://suggestions:50053/get_suggestions"
    try:
        response = requests.get(url)
        response.raise_for_status()
        suggestions_data = response.json()
                
        # Перевірка, чи це список і обробка відповідно
        if isinstance(suggestions_data, list):
            results['suggestions'] = suggestions_data  # Якщо це список
        else:
            results['suggestions'] = suggestions_data.get("bookSuggestions", [])  # Якщо це словник
    except requests.RequestException as e:
        results['suggestions'] = None
        print(f"Error contacting suggestions service: {e}")



# The process_order function to handle the orchestration of the gRPC calls
def process_order(order_data, results):
    # Create threads for gRPC calls
    fraud_thread = threading.Thread(target=check_fraud_api, args=(order_data, results))
    suggestions_thread = threading.Thread(target=get_suggestions_api, args=(results,))  # corrected
    transaction_thread = threading.Thread(target=verify_transaction_api, args=(order_data, results))  # corrected
    # Start threads
    fraud_thread.start()
    transaction_thread.start()
    suggestions_thread.start()

    # Wait for all threads to finish
    fraud_thread.join()
    transaction_thread.join()
    suggestions_thread.join()

@app.get("/checkout")
async def checkout(request: Request):
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    # Get request object data to json
    request_data = await request.json()

    order_data = {
        'orderId': request_data.get('orderId', '12345'),
        'userId': request_data.get('userId', ''),
        'items': request_data.get('items', []),
        'totalAmount': request_data.get('totalAmount', 0.0),
        'cardNumber': request_data.get('cardNumber', '0000000000000000'),
    }
    results = {}

    # Process order (API calls in parallel)
    process_order(order_data, results)

    # Construct response
    order_status_response = {
        'orderId': order_data['orderId'],
        'FraudStatus': results.get('fraud', False),  # Store fraud as a boolean (True/False)
        'transactionStatus': results.get('transaction_valid'),  # Include transaction status
        'suggestedBooks': results.get('suggestions', [])
    }

    return JSONResponse(content=order_status_response)
