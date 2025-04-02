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
sys.path.insert(0, suggestions_path)
sys.path.insert(1, fraud_path)

import books_pb2
import books_pb2_grpc
import fraud_pb2
import fraud_pb2_grpc

# Простий кеш замовлень
order_cache = {}
cache_lock = threading.Lock()

# Ім'я цього сервісу для векторного годинника
SERVICE_NAME = "fraud_service"


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
        #notify_suggestions(order_id, vector_clock)

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
