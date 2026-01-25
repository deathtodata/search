FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY gateway.py .
COPY index.html .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 3000

# Run the gateway
CMD ["python3", "gateway.py"]
