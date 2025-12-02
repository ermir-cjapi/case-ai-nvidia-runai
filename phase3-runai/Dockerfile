# Phase 3 - Standalone GPU Test Application
# Simple Flask app that demonstrates GPU sharing with Run:AI

FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Flask and CUDA utilities
RUN pip3 install flask requests pynvml

# Create app directory
WORKDIR /app

# Copy application
COPY app.py /app/

# Expose port
EXPOSE 8000

# Run the app
CMD ["python3", "app.py"]

