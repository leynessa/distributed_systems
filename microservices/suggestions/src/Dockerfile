FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY suggestions.py /app/suggestions.py


CMD ["python", "suggestions.py"]