FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

CMD ["python", "fraud_detection.py"]