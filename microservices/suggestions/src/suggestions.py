import grpc
from concurrent import futures
import random
import sys
import os
import threading

utils_path = "/app/utils/pb/suggestions"
sys.path.insert(0, utils_path)

import books_pb2
import books_pb2_grpc

SERVICE_NAME = "suggestions_service"
order_cache = {}
cache_lock = threading.Lock()

books_list = [
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "Moby Dick", "author": "Herman Melville"},
    {"title": "War and Peace", "author": "Leo Tolstoy"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
]


def fetch_books_from_list():
    return random.sample(books_list, 2)


class BookService(books_pb2_grpc.BookServiceServicer):
    def GetSuggestions(self, request, context):
        order_id = "default_order"
        incoming_clock = dict(request.vectorClock.clock)

        with cache_lock:
            if order_id not in order_cache:
                order_cache[order_id] = {
                    "vector_clock": {}
                }

            vector_clock = order_cache[order_id]["vector_clock"]

            # Змерджити з вхідним годинником
            for service, ts in incoming_clock.items():
                vector_clock[service] = max(vector_clock.get(service, 0), ts)

            # Перевірка: чи fraud_service завершив
            if vector_clock.get("fraud_service", 0) < 1:
                context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "Cannot provide suggestions before fraud_service completes"
                )

            # Інкрементуємо локальний годинник
            vector_clock[SERVICE_NAME] = vector_clock.get(SERVICE_NAME, 0) + 1

        # Вибір книг
        selected_books = fetch_books_from_list()
        print(f"[OrderID: {order_id}] Vector Clock: {vector_clock}")
        print(f"Books List: {selected_books}")

        # Формуємо відповідь
        response = books_pb2.BookList(
            vectorClock=books_pb2.VectorClock(clock=vector_clock)
        )
        for book in selected_books:
            response.books.add(title=book["title"], author=book["author"])
        return response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    books_pb2_grpc.add_BookServiceServicer_to_server(BookService(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print(f"Book Suggestion Server started. Listening on port 50053")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()