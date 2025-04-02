import grpc
from concurrent import futures
import sys
import random
import threading

utils_path = "/app/utils/pb/fraud_detection"
sys.path.insert(0, utils_path)

import fraud_pb2
import fraud_pb2_grpc

# Простий кеш замовлень
order_cache = {}
cache_lock = threading.Lock()

# Ім'я цього сервісу для векторного годинника
SERVICE_NAME = "fraud_service"

class FraudCheckerServicer(fraud_pb2_grpc.FraudCheckerServicer):
    def CheckFraud(self, request, context):
        order_id = request.orderId
        incoming_clock = dict(request.vectorClock.clock)

        with cache_lock:
            # Якщо замовлення ще не в кеші — ініціалізувати
            if order_id not in order_cache:
                order_cache[order_id] = {
                    "order_data": request,
                    "vector_clock": {}
                }

            vector_clock = order_cache[order_id]["vector_clock"]

            # Змерджити з отриманим вектором
            for service, ts in incoming_clock.items():
                vector_clock[service] = max(vector_clock.get(service, 0), ts)

            # Інкрементувати локальний час
            vector_clock[SERVICE_NAME] = vector_clock.get(SERVICE_NAME, 0) + 1

        is_fraudulent = random.choice([True, False])
        print(f"[OrderID: {order_id}] Vector Clock: {vector_clock}")

        # Побудувати proto-відповідь
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
