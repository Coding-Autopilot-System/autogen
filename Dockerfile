FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromadb dependencies
RUN pip install --no-cache-dir chromadb win11toast

COPY . .

# Expose FastAPI Dashboard
EXPOSE 8000

# Run the watchdog daemon by default
CMD ["python", "scripts/watchdog.py"]
