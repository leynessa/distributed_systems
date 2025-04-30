import grpc
from concurrent import futures
import sys
import threading
import time
import os
from collections import deque
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("order_queue_service")

# Import proto files
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pb/order_queue')))
#sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pb/fraud_detection')))
#sys.path.insert(2, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pb/suggestions')))
#sys.path.insert(3, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../pb/transaction_service')))
transaction_path = "/app/utils/pb/transaction_service"
suggestions_path = "/app/utils/pb/suggestions"
order_queue_path = "/app/utils/pb/order_queue"
fraud_detection_path = "/app/utils/pb/fraud_detection"
books_path = "/app/utils/pb/books_db"
sys.path.insert(0, transaction_path)
sys.path.insert(1, suggestions_path)
sys.path.insert(2, order_queue_path)
sys.path.insert(3, fraud_detection_path)
sys.path.insert(0, books_path)


import order_queue_pb2
import order_queue_pb2_grpc

# Name of this service for vector clock
SERVICE_NAME = "order_queue_service"

# Thread-safe queue
class OrderQueue:
    def __init__(self):
        self.queue = deque()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    
    def enqueue(self, order):
        with self.lock:
            self.queue.append(order)
            position = len(self.queue)
            # Notify any waiting consumers
            self.condition.notify_all()
            return position
    
    def dequeue(self):
        with self.condition:
            # Wait until queue has items
            while len(self.queue) == 0:
                logger.info("Queue is empty, waiting for orders...")
                self.condition.wait()
            
            # Get the next order
            return self.queue.popleft()
    
    def get_size(self):
        with self.lock:
            return len(self.queue)
    
    def get_order_ids(self):
        with self.lock:
            return [order.orderId for order in self.queue]

class OrderQueueServicer(order_queue_pb2_grpc.OrderQueueServiceServicer):
    def __init__(self):
        self.queue = OrderQueue()
        self.order_cache = {}
        self.cache_lock = threading.Lock()
        logger.info("Order Queue Service initialized")
    
    def Enqueue(self, request, context):
        order = request.order
        incoming_clock = dict(request.vectorClock.clock)
        
        with self.cache_lock:
            order_id = order.orderId
            if order_id not in self.order_cache:
                self.order_cache[order_id] = {
                    "vector_clock": {}
                }
            
            vector_clock = self.order_cache[order_id]["vector_clock"]
            # Merge incoming vector clock
            for service, ts in incoming_clock.items():
                vector_clock[service] = max(vector_clock.get(service, 0), ts)
            
            # Increment own time
            vector_clock[SERVICE_NAME] = vector_clock.get(SERVICE_NAME, 0) + 1
        
        position = self.queue.enqueue(order)
        logger.info(f"[OrderID: {order_id}] Enqueued. Queue position: {position}")
        logger.info(f"[OrderID: {order_id}] Vector Clock: {vector_clock}")
        
        return order_queue_pb2.EnqueueResponse(
            success=True,
            message=f"Order {order_id} successfully enqueued",
            queuePosition=position,
            vectorClock=order_queue_pb2.VectorClock(clock=vector_clock)
        )
    
    def Dequeue(self, request, context):
        executor_id = request.executorId
        incoming_clock = dict(request.vectorClock.clock)

        # Create a new merged vector clock for this operation
        operation_clock = {}
        for service, ts in incoming_clock.items():
            operation_clock[service] = ts

        # Increment own time
        operation_clock[SERVICE_NAME] = operation_clock.get(SERVICE_NAME, 0) + 1

        try:
            order = self.queue.dequeue()
            order_id = order.orderId

            with self.cache_lock:
                if order_id in self.order_cache:
                    order_vector_clock = self.order_cache[order_id]["vector_clock"]
                    for service, ts in operation_clock.items():
                        order_vector_clock[service] = max(order_vector_clock.get(service, 0), ts)
                else:
                    order_vector_clock = operation_clock

            logger.info(f"[OrderID: {order_id}] Dequeued by Executor: {executor_id}")
            logger.info(f"[OrderID: {order_id}] Vector Clock: {order_vector_clock}")

            import books_pb2
            import books_pb2_grpc

            channel = grpc.insecure_channel("books_primary:50061")
            books_stub = books_pb2_grpc.BooksDatabaseStub(channel)

            title_quantity_map = {}

            for item in order.items:
                title = item.name
                quantity = item.quantity

                # Step 1: Read current stock
                read_response = books_stub.Read(books_pb2.ReadRequest(title=title))
                current_stock = read_response.stock

                if current_stock == 0:
                    logger.warning(f"[OrderID: {order_id}] Book '{title}' not found or out of stock")
                    return order_queue_pb2.DequeueResponse(
                        success=False,
                        message=f"Book '{title}' not found or out of stock",
                        vectorClock=order_queue_pb2.VectorClock(clock=order_vector_clock)
                    )

                if current_stock < quantity:
                    logger.warning(f"[OrderID: {order_id}] Not enough stock for '{title}': need {quantity}, have {current_stock}")
                    return order_queue_pb2.DequeueResponse(
                        success=False,
                        message=f"Not enough stock for '{title}'",
                        vectorClock=order_queue_pb2.VectorClock(clock=order_vector_clock)
                    )

                title_quantity_map[title] = current_stock - quantity

            # Step 2: Update stock for all items
            for title, new_stock in title_quantity_map.items():
                books_stub.Write(books_pb2.WriteRequest(title=title, new_stock=new_stock))
                logger.info(f"[OrderID: {order_id}] Updated '{title}' to stock={new_stock}")

            success_message = f"Order {order_id} completed successfully"

            return order_queue_pb2.DequeueResponse(
                success=True,
                message=success_message,
                order=order,
                vectorClock=order_queue_pb2.VectorClock(clock=order_vector_clock)
            )

        except Exception as e:
            logger.error(f"Error during dequeue: {str(e)}")
            return order_queue_pb2.DequeueResponse(
                success=False,
                message=f"Error: {str(e)}",
                vectorClock=order_queue_pb2.VectorClock(clock=operation_clock)
            )
    
    def GetQueueStatus(self, request, context):
        incoming_clock = dict(request.vectorClock.clock)
        
        # Create a new vector clock for this operation
        operation_clock = {}
        for service, ts in incoming_clock.items():
            operation_clock[service] = ts
        
        # Increment own time
        operation_clock[SERVICE_NAME] = operation_clock.get(SERVICE_NAME, 0) + 1
        
        queue_size = self.queue.get_size()
        order_ids = self.queue.get_order_ids()
        
        logger.info(f"Queue status requested. Size: {queue_size}")
        logger.info(f"Queue Vector Clock: {operation_clock}")
        
        return order_queue_pb2.QueueStatusResponse(
            queueSize=queue_size,
            orderIds=order_ids,
            vectorClock=order_queue_pb2.VectorClock(clock=operation_clock)
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_queue_pb2_grpc.add_OrderQueueServiceServicer_to_server(OrderQueueServicer(), server)
    server.add_insecure_port('[::]:50054')
    logger.info("Order Queue Service starting on port 50054...")
    server.start()
    print("order queue Server is runing ")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()