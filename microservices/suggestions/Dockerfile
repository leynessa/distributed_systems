# Використовуємо офіційний образ Python
FROM python:3.11

WORKDIR /app

COPY ./microservices/suggestions/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./microservices/suggestions /app/microservices/suggestions

EXPOSE 50053

CMD python -m microservices.suggestions.src.suggestions

