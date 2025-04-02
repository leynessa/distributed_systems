import grpc
from concurrent import futures
import re
import sys
import os
import threading
from datetime import datetime
import calendar

# Proto paths
transaction_path = "/app/utils/pb/transaction_service"
suggestions_path = "/app/utils/pb/suggestions"
sys.path.insert(0, transaction_path)
sys.path.insert(1, suggestions_path)

import transaction_pb2 as transaction_verification
import transaction_pb2_grpc
import books_pb2
import books_pb2_grpc

SERVICE_NAME = "transaction_service"
order_cache = {}
cache_lock = threading.Lock()


def merge_clocks(target, incoming):
    for service, time in incoming.items():
        target[service] = max(target.get(service, 0), time)


def notify_suggestions(order_id, vector_clock):
    """Передає оновлений векторний годинник у suggestions_service."""
    try:
        with grpc.insecure_channel("suggestions:50053") as channel:
            stub = books_pb2_grpc.BookServiceStub(channel)

            request = books_pb2.UpdateClockRequest(
                orderId=order_id,
                vectorClock=books_pb2.VectorClock(clock=vector_clock)
            )

            response = stub.UpdateClock(request)
            updated_clock = dict(response.vectorClock.clock)

            print(f"[OrderID: {order_id}] Notified suggestions_service.")
            print(f"[OrderID: {order_id}] Received updated clock: {updated_clock}")

            # Опційно: змерджити назад у локальний кеш
            for service, ts in updated_clock.items():
                vector_clock[service] = max(vector_clock.get(service, 0), ts)

    except grpc.RpcError as e:
        print(f"[OrderID: {order_id}] Failed to notify suggestions_service: {e.details()}")


def validate_cvv(cvv):
    return bool(re.fullmatch(r"\d{3}", cvv))


def validate_credit_card_number(number):
    return bool(re.fullmatch(r"\d{16}", number))


def validate_required_fields(request):
    missing = []
    if not request.user.name:
        missing.append("user.name")
    if not request.user.contact:
        missing.append("user.contact")
    if not request.creditCard.number:
        missing.append("creditCard.number")
    if not request.creditCard.expirationDate:
        missing.append("creditCard.expirationDate")
    if not request.creditCard.cvv:
        missing.append("creditCard.cvv")
    if not request.billingAddress.street or not request.billingAddress.city or not request.billingAddress.country:
        missing.append("billingAddress")
    if len(request.items) == 0:
        missing.append("items")
    return missing


def validate_expiration_date(date_str):
    if not re.fullmatch(r"\d{2}/\d{2}", date_str):
        return False
    try:
        month, year = map(int, date_str.split("/"))
        year += 2000
        last_day = calendar.monthrange(year, month)[1]
        exp_date = datetime(year, month, last_day)
        return datetime.now() <= exp_date
    except Exception:
        return False


class TransactionService(transaction_pb2_grpc.TransactionServiceServicer):
    def VerifyTransaction(self, request, context):
        order_id = request.orderId
        incoming_clock = dict(request.vectorClock.clock)

        with cache_lock:
            if order_id not in order_cache:
                order_cache[order_id] = {
                    "vector_clock": {}
                }

            vector_clock = order_cache[order_id]["vector_clock"]
            merge_clocks(vector_clock, incoming_clock)
            vector_clock[SERVICE_NAME] = vector_clock.get(SERVICE_NAME, 0) + 1

        print(f"[OrderID: {order_id}] Vector Clock: {vector_clock}")

        if not request.items:
            return transaction_verification.TransactionResponse(isValid=False)

        missing = validate_required_fields(request)
        if missing:
            return transaction_verification.TransactionResponse(isValid=False)

        if not validate_credit_card_number(request.creditCard.number):
            return transaction_verification.TransactionResponse(isValid=False)

        if not validate_expiration_date(request.creditCard.expirationDate):
            return transaction_verification.TransactionResponse(isValid=False)

        if not validate_cvv(request.creditCard.cvv):
            return transaction_verification.TransactionResponse(isValid=False)

        # ✅ Надіслати в suggestions_service
        notify_suggestions(order_id, vector_clock)

        return transaction_verification.TransactionResponse(
            isValid=True,
            vectorClock=transaction_verification.VectorClock(clock=vector_clock)
        )

    def UpdateClock(self, request, context):
        order_id = request.orderId
        incoming_clock = dict(request.vectorClock.clock)

        with cache_lock:
            if order_id not in order_cache:
                order_cache[order_id] = {
                    "vector_clock": {}
                }
            vector_clock = order_cache[order_id]["vector_clock"]
            merge_clocks(vector_clock, incoming_clock)

        print(f"[OrderID: {order_id}] Received clock update from fraud_service.")
        return transaction_verification.UpdateClockResponse(
            vectorClock=transaction_verification.VectorClock(clock=vector_clock)
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transaction_pb2_grpc.add_TransactionServiceServicer_to_server(
        TransactionService(), server
    )
    server.add_insecure_port("[::]:50051")
    print("Transaction Service started on port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
