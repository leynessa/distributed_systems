# Documentation

This folder should contain your documentation, explaining the structure and content of your project. It should also contain your diagrams, explaining the architecture. The recommended writing format is Markdown.


## **System Model**

This system uses a microservices architecture built with FastAPI and gRPC, orchestrated by a central FastAPI service. The components communicate asynchronously, with causal consistency ensured through vector clocks, and fault-tolerant order execution handled by leader election using the Bully algorithm.

### **Characteristics**:
Causal Consistency: Vector clocks enforce service dependencies
Fault Tolerance: Leader election 

### **Communication Flow**:

1. Client sends a **POST** request to `/checkout`.
2. The orchestrator generates a order ID and initializes a vector clock.
3. Services are called in the following order:
   - **Fraud Detection**
   - **Transaction Verification** (after fraud check)
   - **Suggestions** (after transaction check)
   - **Order Queue** (only if fraud = false and transaction = valid)
4. **Vector clocks** are updated and merged at every step to maintain causal consistency.
5. A final response is sent back to the client with the **order status** and **suggestions**.


### **Failure Modes**

- **Service Unavailability:**  
  If any gRPC service is unreachable or fails, the orchestrator marks the order as rejected. The client receives an error message indicating fraud detection or transaction failure.

- **Leader Failure (Order Executors):**  
  If the current leader node becomes unresponsive, the **Bully algorithm** triggers a new election. The node with the highest ID becomes the new leader.

- **Orchestrator Crash:**  
  The orchestrator is **stateless** and easily restartable. Requests in-flight may need to be retried by the client.

- **Causal Order Violation:**  
  Avoided using **vector clocks**, which are merged and propagated between services during and after fraud detection.