import grpc
from concurrent import futures
import random
import sys
import os

# FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
# utils_path = os.path.abspath(os.path.join(FILE, "../../../utils/pb/suggestions"))
utils_path = "/app/utils/pb/suggestions"
sys.path.insert(0, utils_path)

import books_pb2
import books_pb2_grpc

books_list = [
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "Moby Dick", "author": "Herman Melville"},
    {"title": "War and Peace", "author": "Leo Tolstoy"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien"}
]


def fetch_books_from_list():
    return random.sample(books_list, 2)


class BookService(books_pb2_grpc.BookServiceServicer):
    def GetSuggestions(self, request, context):
        response = books_pb2.BookList()
        selected_books = fetch_books_from_list()
        print(f"Books List: {selected_books}")
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