import grpc
from concurrent import futures
import os
import sys
import logging
import random
import time
import threading

FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
order_queue_path = "/app/utils/pb/order_queue"
order_executor_grpc_path = "/app/utils/pb/order_executor"
payment_grpc_path = "/app/utils/pb/payment_service"
database_grpc_path = "/app/utils/pb/books_db"

sys.path.insert(0, order_queue_path)
sys.path.insert(1, order_executor_grpc_path)
sys.path.insert(2, payment_grpc_path)
sys.path.insert(3, database_grpc_path)

import order_executor_pb2_grpc
import order_executor_pb2
import order_queue_pb2
import order_queue_pb2_grpc as order_queue_grpc
import payment_pb2
import payment_pb2_grpc
import books_pb2
import books_pb2_grpc

from google.protobuf.empty_pb2 import Empty

# --- Constants ---
EXECUTOR_PORT_BASE = 50055  # Base port the executors listen on
REPLICA_COUNT = int(os.getenv("ORDER_EXECUTOR_REPLICAS", "3"))
NODE_ID = int(os.getenv("NODE_ID", "1"))  # This node's ID (1-based)
ELECTION_TIMEOUT_SECONDS = 2  # Time to wait for responses during election
RUN_LOOP_SLEEP_SECONDS = 5  # How often to check for orders or leader status

# --- Thread Pool ---
thread_pool = futures.ThreadPoolExecutor(max_workers=10)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("order_executor_service")

# List of all potential executor nodes in the system
EXECUTOR_NODES = {}
for i in range(1, REPLICA_COUNT + 1):
    EXECUTOR_NODES[i] = {
        "host": f"order_executor_{i}",
        "port": EXECUTOR_PORT_BASE + (i - 1),
    }


def get_node_connection(node_id):
    # Get connection string for a node by ID
    if node_id in EXECUTOR_NODES:
        node = EXECUTOR_NODES[node_id]
        return f"{node['host']}:{node['port']}"
    return None


def execute_order(title, quantity, db_stub):
    # Step 1: Read current stock
    response = db_stub.Read(books_pb2.ReadRequest(title=title))
    current_stock = response.stock

    # Step 2: Check stock availability
    if current_stock >= quantity:
        # Step 3: Write updated stock back to the database
        new_stock = current_stock - quantity
        write_response = db_stub.Write(
            books_pb2.WriteRequest(title=title, new_stock=new_stock)
        )
        return write_response.success

    return False  # Not enough stock


class OrderExecutorService(order_executor_pb2_grpc.OrderExecutorServiceServicer):
    def __init__(self):
        self.node_id = NODE_ID
        self.is_leader = False
        self.current_leader = None
        self.election_active = False
        self.election_lock = threading.Lock()

        # Order queue connection
        self.order_queue_stub = order_queue_grpc.OrderQueueServiceStub(
            grpc.insecure_channel("order_queue:50054")
        )

        # Payment connection
        self.payment_stub = payment_pb2_grpc.PaymentServiceStub(
            grpc.insecure_channel("payment:50064")
        )

        # Database connection
        self.database_stub = books_pb2_grpc.BooksDatabaseStub(
            grpc.insecure_channel("books_primary:50061")
        )

        # Start periodic tasks
        threading.Thread(target=self.election_monitor, daemon=True).start()

        # Initial election after a short delay to allow all services to start
        threading.Timer(5.0, self.start_election).start()

    def two_phase_commit(self, order):
        logger.info(f"Order in 2 phase commit: {order}")
        order_id = order.orderId
        amount = order.totalAmount
        title = order.items[0].name
        new_stock = order.items[0].quantity

        ready_votes = []

        # --- PREPARE PHASE ---
        try:
            payment_prepare_resp = self.payment_stub.Prepare(
                payment_pb2.PrepareRequest(order_id=order_id, amount=amount)
            )
            ready_votes.append(payment_prepare_resp.ready)
        except Exception as e:
            logger.warning(f"Payment service prepare failed: {e}")
            ready_votes.append(False)

        try:
            db_prepare_resp = self.database_stub.Prepare(
                books_pb2.TransactionRequest(
                    order_id=order_id,
                    title=title,
                    new_stock=new_stock,
                )
            )
            ready_votes.append(db_prepare_resp.ready)
        except Exception as e:
            logger.warning(f"Database prepare failed: {e}")
            ready_votes.append(False)

        # --- DECISION PHASE ---
        if all(ready_votes):
            logger.info("All participants are ready. Sending COMMIT.")
            try:
                self.payment_stub.Commit(payment_pb2.CommitRequest(order_id=order_id))
            except Exception as e:
                logger.error(f"Error committing to Payment: {e}")

            try:
                self.database_stub.Commit(
                    books_pb2.TransactionRequest(
                        order_id=order_id,
                        title=title,
                        new_stock=new_stock,
                    )
                )
            except Exception as e:
                logger.error(f"Error committing to Database: {e}")

            logger.info("Transaction committed successfully.")
        else:
            logger.warning("Prepare phase failed. Sending ABORT.")
            try:
                self.payment_stub.Abort(payment_pb2.AbortRequest(order_id=order_id))
            except Exception as e:
                logger.error(f"Error aborting on Payment: {e}")

            try:
                self.database_stub.Abort(
                    books_pb2.TransactionRequest(
                        order_id=order_id,
                        title=title,
                        new_stock=new_stock,
                    )
                )
            except Exception as e:
                logger.error(f"Error aborting on Database: {e}")

            logger.info("Transaction aborted.")

    def check_leader_health(self):
        # Check if the current leader is still alive
        if self.current_leader is None or self.current_leader == self.node_id:
            return True

        node_connection = get_node_connection(self.current_leader)
        if not node_connection:
            return False

        try:
            with grpc.insecure_channel(node_connection) as channel:
                stub = order_executor_pb2_grpc.OrderExecutorServiceStub(channel)
                # Use AnnounceID as a health check
                response = stub.AnnounceID(
                    order_executor_pb2.AnnounceRequest(executor_id=self.node_id)
                )
                return True
        except Exception as e:
            logger.warning(f"Leader (Node {self.current_leader}) appears to be down:")
            return False

    def election_monitor(self):
        # Periodically check leader status and start elections if needed
        while True:
            # Check if current leader is still alive
            if not self.check_leader_health():
                logger.info(
                    f"Leader (Node {self.current_leader}) is not responding, starting new election"
                )
                self.current_leader = None
                self.is_leader = False

            # If we don't have a leader and an election is not in progress, start one
            if self.current_leader is None and not self.election_active:
                self.start_election()

            # If we're the leader, run leader duties
            if self.is_leader:
                self.perform_leader_duties()

            time.sleep(RUN_LOOP_SLEEP_SECONDS)

    def start_election(self):
        # Start a leader election using the Bully Algorithm
        with self.election_lock:
            if self.election_active:
                return
            self.election_active = True
            self.current_leader = None
            self.is_leader = False  # Reset leader status when starting election

        logger.info(f"Starting election process from node {self.node_id}")
        higher_nodes_responded = False

        # Contact all nodes with higher IDs
        for node_id in EXECUTOR_NODES:
            if node_id > self.node_id:
                node_connection = get_node_connection(node_id)
                if node_connection:
                    try:
                        with grpc.insecure_channel(node_connection) as channel:
                            stub = order_executor_pb2_grpc.OrderExecutorServiceStub(
                                channel
                            )
                            response = stub.AnnounceID(
                                order_executor_pb2.AnnounceRequest(
                                    executor_id=self.node_id
                                )
                            )
                            higher_nodes_responded = True
                            logger.info(
                                f"Higher node {node_id} acknowledged election message"
                            )
                    except Exception as e:
                        logger.warning(f"Could not contact node {node_id}: {e}")

        # If no higher nodes responded, declare self as leader
        if not higher_nodes_responded:
            self.become_leader()
        else:
            # Wait for a coordinator message from a higher node
            def check_for_leader():
                time.sleep(ELECTION_TIMEOUT_SECONDS)
                with self.election_lock:
                    if self.current_leader is None:
                        # No leader was declared, start a new election
                        self.election_active = False
                        self.start_election()
                    else:
                        self.election_active = False

            threading.Thread(target=check_for_leader, daemon=True).start()

    def become_leader(self):
        # Declare this node as the leader and notify all other nodes
        self.is_leader = True
        self.current_leader = self.node_id
        # logger.info(
        #     f" NEW LEADER ELECTED: Node {self.node_id} is now the leader of the cluster"
        # )

        # Notify all other nodes about the new leader
        for node_id in EXECUTOR_NODES:
            if node_id != self.node_id:
                node_connection = get_node_connection(node_id)
                if node_connection:
                    try:
                        with grpc.insecure_channel(node_connection) as channel:
                            stub = order_executor_pb2_grpc.OrderExecutorServiceStub(
                                channel
                            )
                            response = stub.CoordinatorAnnouncement(
                                order_executor_pb2.CoordinatorMessage(
                                    leader_id=self.node_id
                                )
                            )
                            if response.acknowledged:
                                logger.info(
                                    f"Node {node_id} acknowledged Node {self.node_id} as the new leader"
                                )
                    except Exception as e:

                        logger.warning(f"Could not notify node ]")

        with self.election_lock:
            self.election_active = False

    def perform_leader_duties(self):
        # Main loop that runs when this node is the leader
        logger.info(f"Performing leader duties for node {self.node_id}")
        if not self.is_leader:
            return

        try:
            # Dequeue an order from the order queue
            response = self.order_queue_stub.Dequeue(
                order_queue_pb2.DequeueRequest(
                    executorId=str(self.node_id),
                    vectorClock=order_queue_pb2.VectorClock(),  # Initialize with empty vector clock
                )
            )
            logger.info(f"Dequeued order: {response}")
            if response.success:
                logger.info(f"Dequeued order: {response.order.orderId}")
                logger.info(f"Order is being executed... ")
                logger.info(f"Order: {response.order}")
                self.two_phase_commit(response.order)
            else:
                # No orders in queue
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in leader duties: {e}")

    # gRPC service methods
    def AnnounceID(self, request, context):
        # Handle election announcement from another node
        candidate_id = request.executor_id
        logger.info(f"Received election announcement from node {candidate_id}")

        # If we receive an announcement from a lower ID, we start our own election
        if candidate_id < self.node_id:
            self.start_election()

        # Always acknowledge to let the sender know we're alive
        return Empty()

    def CoordinatorAnnouncement(self, request, context):
        """Handle coordinator announcement from the newly elected leader"""
        leader_id = request.leader_id
        logger.info(
            f"Received coordinator announcement: Node {leader_id} claims leadership"
        )

        # Only accept leadership from higher nodes or if we're not already a leader
        if leader_id > self.node_id or not self.is_leader:
            self.current_leader = leader_id
            self.is_leader = leader_id == self.node_id
            logger.info(
                f"LEADER ACKNOWLEDGED: Node {leader_id} is confirmed as the cluster leader"
            )
            return order_executor_pb2.CoordinatorResponse(acknowledged=True)

        logger.warning(
            f"Rejected leadership claim from Node {leader_id} as we are already the leader"
        )
        return order_executor_pb2.CoordinatorResponse(acknowledged=False)


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add OrderExecutorService
    order_executor_pb2_grpc.add_OrderExecutorServiceServicer_to_server(
        OrderExecutorService(), server
    )

    # Listen on port from environment or default
    port = os.getenv("LISTENING_PORT", str(EXECUTOR_PORT_BASE + NODE_ID - 1))
    server.add_insecure_port(f"[::]:{port}")

    # Start the server
    server.start()
    logger.info(f"Server started. Listening on port {port}. Node ID: {NODE_ID}")

    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
