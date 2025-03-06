import grpc
from concurrent import futures
import random


from . import books_pb2
from . import books_pb2_grpc

# Example book list
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

class BookService(books_pb2_grpc.BookServiceServicer):
    def GetSuggestions(self, request, context):
        num_suggestions = 3
        if len(books_list) < num_suggestions:
            num_suggestions = len(books_list)
        
        selected_books = random.sample(books_list, num_suggestions)
        response = books_pb2.BookList()
        
        for book in selected_books:
            response.books.add(title=book["title"], author=book["author"])
        
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    books_pb2_grpc.add_BookServiceServicer_to_server(BookService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    print(1.2)
    serve()

