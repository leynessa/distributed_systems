FROM python:3.11

WORKDIR /app

COPY ./microservices/transaction_verification/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./microservices/transaction_verification /app/microservices/transaction_verification

EXPOSE 50052

CMD python -m microservices.transaction_verification.src.transaction_verification
