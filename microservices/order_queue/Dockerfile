# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
# Both the utils and src folders will be mounted as volumes, please see docker-compose.yaml
WORKDIR /app

# Copy the requirements file to the working directory
COPY ./microservices/order_queue/requirements.txt .

COPY ./microservices/order_queue /app/microservices/order_queue

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade protobuf

EXPOSE 50054

# Set the command to run the application
CMD python utils/other/hotreload.py "microservices/order_queue/src/order_queue.py"