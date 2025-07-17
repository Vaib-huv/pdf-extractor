FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Run the application
CMD ["python", "main.py"]
