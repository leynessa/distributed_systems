import requests
import json

# Створення даних для запиту
order_data = {
    'orderId': '12345',
    'userId': 'user001',
    'items': [
        {'itemId': 'item001', 'quantity': 2, 'price': 20.5},
        {'itemId': 'item002', 'quantity': 1, 'price': 10.0}
    ],
    'totalAmount': 51.0,
    'cardNumber': '1234567890123456'  
}

# Переклад даних в JSON
json_data = json.dumps(order_data)

# Відправка GET запиту з JSON даними
url = "http://localhost:8081/checkout"
headers = {'Content-Type': 'application/json'}

# Відправляємо GET запит з параметрами в тілі
response = requests.get(url, headers=headers, data=json_data)

# Перевірка статусу відповіді
if response.status_code == 200:
    print("Запит успішний. Отримано відповідь:")
    print(response.json())  # Вивести відповідь у вигляді JSON
else:
    print(f"Помилка запиту. Статус код: {response.status_code}")
