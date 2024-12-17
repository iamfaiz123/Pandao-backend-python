# Builder stage: Install dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Rust and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libssl-dev \
    libffi-dev \
    rustc \
    cargo \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Application stage: Create the runtime image
FROM python:3.10-slim AS runner

WORKDIR /app

# Copy installed dependencies and application files from builder
COPY --from=builder /app /app

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
