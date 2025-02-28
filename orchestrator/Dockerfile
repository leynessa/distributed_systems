# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's cache for dependencies
COPY ./orchestrator/requirements.txt /app/requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory to the working directory
COPY . /app

# Set the command to run the container
CMD ["python", "/app/utils/other/hotreload.py", "/app/orchestrator/src/app.py"]