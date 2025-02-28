# transaction_verification/Dockerfile
FROM python:3.11
WORKDIR /app
COPY ./transaction_verification/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "/app/utils/other/hotreload.py", "/app/transaction_verification/src/app.py"]