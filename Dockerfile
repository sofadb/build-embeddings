FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the embedding script
COPY build_embeddings.py .

# Make script executable
RUN chmod +x build_embeddings.py

# Create mount points
VOLUME ["/docs", "/embeddings"]

# Run the script
CMD ["python", "build_embeddings.py"]
