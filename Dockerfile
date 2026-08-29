# ==========================================
# Base Python image
# ==========================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck, libpq for psycopg2 if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy production requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python production dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 5000

# Run database migrations and start Gunicorn server
CMD ["sh", "-c", "flask db upgrade && gunicorn run:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120"]
