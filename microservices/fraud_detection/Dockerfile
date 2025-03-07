# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
# Both the utils and src folders will be mounted as volumes, please see docker-compose.yaml
WORKDIR /app

# Copy the requirements file to the working directory
COPY ./microservices/fraud_detection/requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 50051

# Set the command to run the application
CMD python -m microservices.fraud_detection.src.fraud_detection