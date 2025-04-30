# Use an official Python runtime as the base image
FROM python:3.11

# Set working directory inside the container
WORKDIR /app

# Optionally: copy requirements if ти хочеш винести залежності в requirements.txt
# COPY ./microservices/books_db/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Встановлюємо напряму для простоти (або можна через reqs)
RUN pip install --no-cache-dir grpcio grpcio-tools

# Копіювати нічого не треба — код буде змонтовано через volume
# CMD виконується через docker-compose, тому тут нічого

# Однак можна лишити дефолт на випадок локального запуску
CMD ["python", "microservices/books_db/src/replica.py"]
