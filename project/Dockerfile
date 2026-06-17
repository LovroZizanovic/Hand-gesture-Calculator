# Start with a clean Python environment
FROM python:3.10-slim

# Prevent Python from buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Linux graphical and camera libraries inside the container isolation
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory inside the container
WORKDIR /app

# Install dependencies from your requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual Python code files into the container
COPY . .

# Run your program
CMD ["python", "main.py"]