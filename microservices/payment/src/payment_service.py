import grpc
from concurrent import futures
import os
import sys

# Path to books proto
payment_proto_path = "/app/utils/pb/payment_service"
sys.path.insert(0, payment_proto_path)

# Imports after setting the path
import payment_pb2
import payment_pb2_grpc


class PaymentService(payment_pb2_grpc.PaymentService):
    def __init__(self):
        self.prepared = {}

    def Prepare(self, request, context):
        order_id = request.order_id
        self.prepared[order_id] = True
        return payment_pb2.PrepareResponse(ready=True)

    def Commit(self, request, context):
        order_id = request.order_id
        if self.prepared.get(order_id, False):
            print(f"Payment committed for order {order_id}")
            del self.prepared[order_id]
            return payment_pb2.CommitResponse(success=True)
        return payment_pb2.CommitResponse(success=False)

    def Abort(self, request, context):
        order_id = request.order_id
        if order_id in self.prepared:
            del self.prepared[order_id]
        print(f"Payment aborted for order {order_id}")
        return payment_pb2.AbortResponse(aborted=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentService(), server)
    server.add_insecure_port("[::]:50064")
    server.start()
    print("Payment Service is running on port 50064...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
