# Використовуємо офіційний образ Python
FROM python:3.11

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файл залежностей
COPY ./microservices/suggestions/requirements.txt .

# Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код мікросервісу
COPY ./microservices/suggestions /app/microservices/suggestions

# Виставляємо порт (gRPC за замовчуванням працює на 50051)
EXPOSE 50053

# Команда для запуску gRPC-сервера
CMD ["python", "-m", "microservices.suggestions.src.suggestions"]

