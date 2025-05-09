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
    test_title = "Book A"
    new_stock = 42

    # опційна пауза, щоб дати час на реплікацію

    print(f"[TEST] Reading '{test_title}'")
    read_response = stub.Read(books_pb2.ReadRequest(title=test_title))
    print(f"[READ RESPONSE] stock = {read_response.stock}")


if __name__ == "__main__":
    main()
