import grpc
import sys
import time

import books_pb2
import books_pb2_grpc

def main():
    # Підключення до primary (порт 50061, як у docker-compose)
    channel = grpc.insecure_channel("localhost:50061")
    stub = books_pb2_grpc.BooksDatabaseStub(channel)

    # Параметри для тесту
    test_title = "The Little Prince"
    new_stock = 42

    print(f"[TEST] Writing '{test_title}' with stock={new_stock}")
    write_response = stub.Write(
        books_pb2.WriteRequest(title=test_title, new_stock=new_stock)
    )
    print(f"[WRITE RESPONSE] success = {write_response.success}")

    time.sleep(1)  # опційна пауза, щоб дати час на реплікацію

    print(f"[TEST] Reading '{test_title}'")
    read_response = stub.Read(
        books_pb2.ReadRequest(title=test_title)
    )
    print(f"[READ RESPONSE] stock = {read_response.stock}")

    # Перевірка
    assert read_response.stock == new_stock, "Stock value mismatch!"
    print("✅ Test passed: value written and read successfully.")

if __name__ == "__main__":
    main()
