import requests
import json

# Creating data for the request
order_data = {
    'orderId': '12345',
    'userId': 'user001',
    'items': [
        {'itemId': 'item001', 'quantity': 2, 'price': 20.5},
        {'itemId': 'item002', 'quantity': 1, 'price': 10.0}
    ],
    'totalAmount': 51.0,
    'creditCard': {
        'number': '4111111111111111',
        'expirationDate': '12/25',
        'cvv': '123'
    }
}

# Converting data to JSON
json_data = json.dumps(order_data)

# Sending a GET request with JSON data
url = "http://localhost:8081/checkout"
headers = {'Content-Type': 'application/json'}

# Sending a GET request with parameters in the body
response = requests.post(url, headers=headers, data=json_data)

# Checking the response status
if response.status_code == 200:
    print("Request successful. Response received:")
    print(response.json())  # Print the response as JSON
else:
    print(f"Bad request. Status code: {response.status_code}")

