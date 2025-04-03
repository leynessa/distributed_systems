import grpc
from concurrent import futures
import sys
import random
import threading
import time
import os

# Додаємо шлях до suggestions proto
suggestions_path = "/app/utils/pb/suggestions"
fraud_path = "/app/utils/pb/fraud_detection"
transaction_path = "/app/utils/pb/transaction_service"

sys.path.insert(0, suggestions_path)
sys.path.insert(1, fraud_path)
sys.path.insert(2, transaction_path)

import books_pb2
import books_pb2_grpc
import fraud_pb2
import fraud_pb2_grpc
import transaction_pb2
import transaction_pb2_grpc

# Простий кеш замовлень
order_cache = {}
cache_lock = threading.Lock()

# Ім'я цього сервісу для векторного годинника
SERVICE_NAME = "fraud_service"


def notify_services(order_id, vector_clock):
    """Надсилає оновлений векторний годинник до suggestions_service і transaction_service."""
    services = [
        ("suggestions:50053", books_pb2_grpc.BookServiceStub, books_pb2.UpdateClockRequest, books_pb2.VectorClock),
        ("transaction_verification:50052", transaction_pb2_grpc.TransactionServiceStub, transaction_pb2.UpdateClockRequest, transaction_pb2.VectorClock),
    ]

    for address, stub_class, request_class, clock_class in services:
        try:
            with grpc.insecure_channel(address) as channel:
                stub = stub_class(channel)

                request = request_class(
                    orderId=order_id,
                    vectorClock=clock_class(clock=vector_clock)
                )

                response = stub.UpdateClock(request)
                updated_clock = dict(response.vectorClock.clock)

                print(f"[OrderID: {order_id}] Notified {address.split(':')[0]}")
                print(f"[OrderID: {order_id}] Received updated clock: {updated_clock}")

                # Змерджити назад у локальний кеш
                for service, ts in updated_clock.items():
                    vector_clock[service] = max(vector_clock.get(service, 0), ts)

        except grpc.RpcError as e:
            print(f"[OrderID: {order_id}] Failed to notify {address.split(':')[0]}: {e.details()}")



class FraudCheckerServicer(fraud_pb2_grpc.FraudCheckerServicer):
    def CheckFraud(self, request, context):
        order_id = request.orderId
        incoming_clock = dict(request.vectorClock.clock)

        with cache_lock:
            if order_id not in order_cache:
                order_cache[order_id] = {
                    "order_data": request,
                    "vector_clock": {}
                }

            vector_clock = order_cache[order_id]["vector_clock"]

            # Мерджимо отриманий годинник
            for service, ts in incoming_clock.items():
                vector_clock[service] = max(vector_clock.get(service, 0), ts)

            # Інкрементуємо власний час
            vector_clock[SERVICE_NAME] = vector_clock.get(SERVICE_NAME, 0) + 1

        is_fraudulent = random.choice([True, False])
        print(f"[OrderID: {order_id}] Vector Clock: {vector_clock}")
        time.sleep(3)
        # ⏭️ Після обробки — повідомляємо suggestions_service
        notify_services(order_id, vector_clock)

        return fraud_pb2.FraudResponse(
            isFraudulent=is_fraudulent,
            vectorClock=fraud_pb2.VectorClock(clock=vector_clock)
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    fraud_pb2_grpc.add_FraudCheckerServicer_to_server(FraudCheckerServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server is running on port 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
