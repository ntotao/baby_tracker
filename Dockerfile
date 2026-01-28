FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (sqlite3 needed for some operations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition
COPY pyproject.toml README.md ./

# Install dependencies
# We use pip to install the package in editable mode or just dependencies
RUN pip install --no-cache-dir .

# Copy source code
COPY src ./src

# Create data directory
RUN mkdir -p data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port for FastAPI
EXPOSE 8000

# Command to run
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
