import grpc
from concurrent import futures
import os
import sys

# Path to books proto
books_proto_path = "/app/utils/pb/books_db"
sys.path.insert(0, books_proto_path)

# Imports after setting the path
import books_pb2
import books_pb2_grpc


# Base class for all replicas (both primary and backup)
class BooksDatabaseServicer(books_pb2_grpc.BooksDatabaseServicer):
    def __init__(self):
        self.store = {}

    def Read(self, request, context):
        stock = self.store.get(request.title, 0)
        print(f"[READ] '{request.title}' => {stock}")
        return books_pb2.ReadResponse(stock=stock)

    def Write(self, request, context):
        self.store[request.title] = request.new_stock
        print(f"[WRITE] '{request.title}' => {request.new_stock}")
        return books_pb2.WriteResponse(success=True)

    def DecrementStock(self, request, context):
        """Decrement stock by a specified amount."""
        current_stock = self.store.get(request.title, 0)
        new_stock = current_stock - request.amount

        if new_stock < 0:
            # Prevent negative stock
            new_stock = 0

        self.store[request.title] = new_stock
        print(
            f"[DECREMENT] '{request.title}' => {new_stock} (Decreased by {request.amount})"
        )
        return books_pb2.WriteResponse(success=True)

    def IncrementStock(self, request, context):
        """Increment stock by a specified amount."""
        current_stock = self.store.get(request.title, 0)
        new_stock = current_stock + request.amount

        self.store[request.title] = new_stock
        print(
            f"[INCREMENT] '{request.title}' => {new_stock} (Increased by {request.amount})"
        )
        return books_pb2.WriteResponse(success=True)


# Primary replica: propagates Write to backups
class PrimaryReplica(BooksDatabaseServicer):
    def __init__(self, backup_stubs):
        super().__init__()
        self.backups = backup_stubs
        self.temp_updates = {}

    def Prepare(self, request, context):
        # Check if there is enough stock
        current_stock = self.store.get(request.title, 0)
        needed_stock = (
            request.new_stock
        )  # This should be the new stock after order, so we need to know the quantity ordered
        quantity_ordered = current_stock - needed_stock

        if current_stock >= quantity_ordered:
            print(f"[PREPARE] Staging update for order {request.order_id}")
            self.temp_updates[request.order_id] = (request.title, needed_stock)
            return books_pb2.PrepareResponse(ready=True)
        else:
            print(
                f"[PREPARE] Not enough stock for order {request.order_id}: '{request.title}' (have {current_stock}, need {quantity_ordered})"
            )
            return books_pb2.PrepareResponse(ready=False)

    def Commit(self, request, context):
        update = self.temp_updates.pop(request.order_id, None)
        if update:
            title, new_stock = update
            self.store[title] = new_stock
            print(f"[COMMIT] Applied update: '{title}' => {new_stock}")

            # Propagate to backups
            for backup in self.backups:
                try:
                    backup.Write(
                        books_pb2.WriteRequest(title=title, new_stock=new_stock)
                    )
                    print(f"  ↳ Replicated to backup OK")
                except Exception as e:
                    print(f"  ↳ Failed to replicate to backup: {e}")

            return books_pb2.CommitResponse(
                success=True, message="Transaction committed successfully"
            )
        else:
            return books_pb2.CommitResponse(
                success=False, message="Transaction not found"
            )

    def Abort(self, request, context):
        print(f"[ABORT] Discarding staged update for order {request.order_id}")
        self.temp_updates.pop(request.order_id, None)
        return books_pb2.AbortResponse(
            aborted=True, message="Transaction aborted successfully"
        )

    def Write(self, request, context):
        self.store[request.title] = request.new_stock
        print(f"[PRIMARY WRITE] '{request.title}' => {request.new_stock}")

        for backup in self.backups:
            try:
                backup.Write(request)
                print(f"  ↳ Replicated to backup OK")
            except Exception as e:
                print(f"  ↳ Failed to replicate to backup: {e}")

        return books_pb2.WriteResponse(success=True)


# Launch the gRPC server
def serve(role, port, backup_ports=None):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    if role == "primary":
        backup_stubs = []
        for p in backup_ports:
            ch = grpc.insecure_channel(f"books_backup{p - 50061}:{p}")
            stub = books_pb2_grpc.BooksDatabaseStub(ch)
            backup_stubs.append(stub)
        servicer = PrimaryReplica(backup_stubs)
    else:
        servicer = BooksDatabaseServicer()

    books_pb2_grpc.add_BooksDatabaseServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[{role.upper()}] Replica running on port {port}")
    server.wait_for_termination()


# Entry point: read from os.environ (instead of sys.argv)
if __name__ == "__main__":
    role = os.environ.get("REPLICA_ROLE", "backup")
    port = int(os.environ.get("LISTENING_PORT", 50061))

    backup_ports_str = os.environ.get("BACKUP_PORTS", "")
    backup_ports = (
        list(map(int, backup_ports_str.split(",")))
        if role == "primary" and backup_ports_str
        else None
    )

    serve(role, port, backup_ports)
