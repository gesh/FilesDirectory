# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install curl and sqlite3
RUN apt-get update && apt-get install -y curl sqlite3 && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for the database
RUN mkdir -p /app/instance

# Expose port 5555
EXPOSE 5555

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Run the application directly with python
CMD ["python", "app.py"] 