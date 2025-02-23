from fastapi import FastAPI
from pydantic import BaseModel
import random

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

@app.get("/get_suggestions")
def get_suggestions():
    num_suggestions = 3  # Кількість книг для повернення
    if len(books_list) < num_suggestions:
        num_suggestions = len(books_list)
    
    return random.sample(books_list, num_suggestions)
