import grpc
import time
import books_pb2
import books_pb2_grpc


def test_book_write_and_read(stub, title, new_stock):
    print(f"\n[TEST] Writing '{title}' with stock = {new_stock}")
    try:
        write_response = stub.Write(
            books_pb2.WriteRequest(title=title, new_stock=new_stock)
        )
        print(f"[WRITE RESPONSE] success = {write_response.success}")
    except grpc.RpcError as e:
        print(f"[ERROR] Write failed for '{title}': {e.code()} - {e.details()}")
        return

    time.sleep(0.5)  # Optional delay for replication/stability

    print(f"[TEST] Reading '{title}'")
    try:
        read_response = stub.Read(books_pb2.ReadRequest(title=title))
        print(f"[READ RESPONSE] stock = {read_response.stock}")

        if read_response.stock == new_stock:
            print("[SUCCESS] Read value matches written value.")
        else:
            print("[WARNING] Mismatch: read stock != written stock")

    except grpc.RpcError as e:
        print(f"[ERROR] Read failed for '{title}': {e.code()} - {e.details()}")


def main():
    # Connect to the database service
    channel = grpc.insecure_channel("localhost:50061")
    stub = books_pb2_grpc.BooksDatabaseStub(channel)

    # Test parameters for Book A and Book B
    test_books = {
        "Book A": 42,
        "Book B": 17,
    }

    # Run tests for each book
    for title, stock in test_books.items():
        test_book_write_and_read(stub, title, stock)


if __name__ == "__main__":
    main()
