from fastapi import FastAPI
from pydantic import BaseModel
import random
import requests

app = FastAPI()

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

class SuggestionsRequest(BaseModel):
    preferences: list

class SuggestionsResponse(BaseModel):
    bookSuggestions: list

@app.post("/get_suggestions", response_model=SuggestionsResponse)
def get_suggestions(request: SuggestionsRequest):
    # For simplicity, select a random subset of books to suggest
    num_suggestions = 3  # You can adjust how many books to suggest
    suggested_books = random.sample(books_list, num_suggestions)
    return SuggestionsResponse(bookSuggestions=suggested_books)
