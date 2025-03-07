import grpc
from concurrent import futures
import json
from openai import OpenAI
import re

from . import books_pb2
from . import books_pb2_grpc

import os
from dotenv import load_dotenv

load_dotenv()


OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
ai_client = OpenAI(api_key=OPEN_AI_API_KEY)

def fetch_books_from_gpt():
    try:
        prompt = """Please provide a JSON array containing exactly two RANDOM books, chosen from different genres or time periods.
        Each book should be an object with 'title' and 'author' fields.
        The response should be a valid JSON array with two such objects.
        Example: [{\"title\": \"The Title\", \"author\": \"Firstname Secondname\"},
        {\"title\": \"The Title\", \"author\": \"Firstname Secondname\"}].""" 
        messages = [{"role": "user", "content": prompt}]
        response = ai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        response_content = response.choices[0].message.content.strip()
        print(response_content)
        cleaned_content = re.sub(r"```json\n(.*?)\n```", r"\1", response_content, flags=re.DOTALL).strip()

        books_json = json.loads(cleaned_content)
        if isinstance(books_json, list) and len(books_json) == 2:
            return books_json
    except Exception as e:
        print(f"Error fetching books from GPT: {e}")
    return []

class BookService(books_pb2_grpc.BookServiceServicer):
    def GetSuggestions(self, request, context):
        response = books_pb2.BookList()
        for book in fetch_books_from_gpt():
            response.books.add(title=book["title"], author=book["author"])
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    books_pb2_grpc.add_BookServiceServicer_to_server(BookService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()


"""
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
    serve()
"""
