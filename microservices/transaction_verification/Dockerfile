FROM python:3.11

WORKDIR /app

COPY ./microservices/transaction_verification/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./microservices/transaction_verification /app/microservices/transaction_verification
RUN pip install --upgrade protobuf
EXPOSE 50052

CMD python utils/other/hotreload.py "microservices/transaction_verification/src/transaction_verification.py"
