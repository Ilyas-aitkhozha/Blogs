FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# probrasivau порт UVicorn
EXPOSE 8000

# FastAPI из tickets.main
CMD ["uvicorn", "tickets.main:app", "--host", "0.0.0.0", "--port", "8000"]
