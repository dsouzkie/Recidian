FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/
COPY static/ ./static/
COPY README.md .

# Expose port for FastAPI
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
